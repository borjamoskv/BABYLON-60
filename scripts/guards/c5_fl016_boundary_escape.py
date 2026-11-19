#!/usr/bin/env python3
"""
c5_fl016_boundary_escape.py - Protocolo Experimental FL-016 v1.0.2 (Deadlock Free)
Estándar C5-REAL / Mandatory Access Control en Darwin APFS

Correcciones de Silicio:
1. Re-entrant Lock: self._journal_lock migrado a threading.RLock() para permitir llamadas
   anidadas a append_journal_block() durante el recovery protocol.
2. Canonical Jail Root: os.path.realpath() aísla los symlinks del contenedor de los de macOS (/var).
"""

import os
import sys
import time
import errno
import fcntl
import stat
import hashlib
import tempfile
import threading
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path


class BoundaryEscapeViolation(Exception):
    pass


class E5BrokerKernel:
    def __init__(self, vault_dir: str, journal_path: str):
        self.vault_dir = os.path.realpath(vault_dir)
        self.journal_path = os.path.realpath(journal_path)
        self._lock_path = f"{self.journal_path}.lock"
        # RLock reentrante para soportar llamadas anidadas en transacciones de recovery
        self._journal_lock = threading.RLock()
        self._process_lock_depth = 0
        self._last_block_hash = "0" * 64
        self._consumed_tokens = set()
        self._revoked_tokens = set()
        with self._transaction_lock():
            pass

    @contextmanager
    def _transaction_lock(self):
        with self._journal_lock:
            outermost = self._process_lock_depth == 0
            if outermost:
                fd = os.open(self._lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX)
                    self._load_journal_state()
                except BaseException:
                    os.close(fd)
                    raise
            self._process_lock_depth += 1
            try:
                yield
            finally:
                self._process_lock_depth -= 1
                if outermost:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                    os.close(fd)

    def _load_journal_state(self):
        self._last_block_hash = "0" * 64
        self._consumed_tokens.clear()
        self._revoked_tokens.clear()
        if os.path.exists(self.journal_path):
            if not self._audit_journal_integrity():
                raise BoundaryEscapeViolation("Journal corrupto al reanudar")
            with open(self.journal_path, "rb") as journal:
                for line in journal:
                    parts = line.split()
                    self._last_block_hash = parts[0].decode("ascii")
                    action, token_id = parts[2].decode("ascii"), parts[3].decode("ascii")
                    if action == "BEGIN":
                        self._consumed_tokens.add(token_id)
                    elif action == "REVOKE":
                        self._revoked_tokens.add(token_id)

    def _sync_parent_dir(self, file_path: str):
        parent_fd = os.open(os.path.dirname(file_path), os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)

    def verify_no_symlink_in_jail(self, target_path: str):
        clean_target = os.path.abspath(target_path)
        if os.path.commonpath((self.vault_dir, clean_target)) != self.vault_dir:
            raise BoundaryEscapeViolation(f"Path escape fuera del vault: {clean_target}")

        rel_path = os.path.relpath(clean_target, self.vault_dir)
        parts = rel_path.split(os.sep)

        current = self.vault_dir
        for part in parts:
            if not part or part == ".":
                continue
            current = os.path.join(current, part)
            if os.path.islink(current):
                raise BoundaryEscapeViolation(f"Symlink detectado en componente interno: {current}")

    def append_journal_block(
        self, action: str, token_id: str, payload_hash: str, filename: str = "", prior_state: str = "-"
    ) -> str:
        with self._transaction_lock():
            ts = time.time()
            encoded_name = filename.encode("utf-8").hex() or "-"
            data_to_hash = (
                f"{self._last_block_hash}:{action}:{token_id}:{payload_hash}:{ts}:{encoded_name}:{prior_state}".encode()
            )
            block_hash = hashlib.sha256(data_to_hash).hexdigest()
            line = f"{block_hash} {self._last_block_hash} {action} {token_id} {payload_hash} {ts} {encoded_name} {prior_state}\n"

            with open(self.journal_path, "a") as j:
                j.write(line)
                j.flush()
                os.fsync(j.fileno())

            self._sync_parent_dir(self.journal_path)
            self._last_block_hash = block_hash
            return block_hash

    def audit_journal_integrity(self) -> bool:
        try:
            with self._transaction_lock():
                return self._audit_journal_integrity()
        except BoundaryEscapeViolation:
            return False

    def _audit_journal_integrity(self) -> bool:
        if not os.path.exists(self.journal_path):
            return True
        last_hash = "0" * 64
        with open(self.journal_path, "r") as j:
            for line in j:
                parts = line.strip().split()
                if len(parts) != 8:
                    return False
                b_hash, prev_hash, action, tok, p_hash, ts, encoded_name, prior_state = parts
                if prev_hash != last_hash:
                    return False
                recomputed = hashlib.sha256(
                    f"{prev_hash}:{action}:{tok}:{p_hash}:{ts}:{encoded_name}:{prior_state}".encode()
                ).hexdigest()
                if recomputed != b_hash:
                    return False
                last_hash = b_hash
        return True

    def revoke_token(self, token_id: str):
        with self._transaction_lock():
            self._revoked_tokens.add(token_id)
            self.append_journal_block("REVOKE", token_id, "NONE")

    def execute_mediated_effect(
        self, token_id: str, filename: str, content: bytes, inject_crash_after_effect: bool = False
    ) -> bool:
        if (
            not filename
            or filename in (".", "..")
            or os.path.basename(filename) != filename
            or filename.startswith((".tmp_", ".bak_"))
            or any(c in filename for c in "\r\n\x00")
            or re.fullmatch(r"[A-Za-z0-9_-]+", token_id) is None
        ):
            return False
        target_path = os.path.join(self.vault_dir, filename)
        temp_path = os.path.join(self.vault_dir, f".tmp_{token_id}")
        backup_path = os.path.join(self.vault_dir, f".bak_{token_id}")
        p_hash = hashlib.sha256(content).hexdigest()

        with self._transaction_lock():
            try:
                self.verify_no_symlink_in_jail(target_path)
            except BoundaryEscapeViolation:
                return False
            if token_id in self._consumed_tokens or token_id in self._revoked_tokens:
                return False
            prior_state = "EXISTED" if os.path.lexists(target_path) else "ABSENT"
            if prior_state == "EXISTED":
                try:
                    fd = os.open(target_path, os.O_RDONLY | os.O_NOFOLLOW)
                except OSError:
                    return False
                try:
                    if not stat.S_ISREG(os.fstat(fd).st_mode):
                        return False
                finally:
                    os.close(fd)
            self._consumed_tokens.add(token_id)
            self.append_journal_block("BEGIN", token_id, p_hash, filename, prior_state)
            try:
                if prior_state == "EXISTED":
                    os.link(target_path, backup_path, follow_symlinks=False)
                    self._sync_parent_dir(backup_path)
                self.append_journal_block("PREPARED", token_id, p_hash, filename)

                fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "wb") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                self._sync_parent_dir(temp_path)

                os.replace(temp_path, target_path)
                self._sync_parent_dir(target_path)
            except Exception:
                if os.path.lexists(temp_path):
                    os.remove(temp_path)
                return False

            if inject_crash_after_effect:
                return False

            self.append_journal_block("COMMIT", token_id, p_hash, filename)
            if os.path.lexists(backup_path):
                try:
                    os.remove(backup_path)
                    self._sync_parent_dir(backup_path)
                except OSError:
                    # El COMMIT ya es durable; recovery retirará el respaldo.
                    pass
            return True

    def recovery_protocol(self):
        with self._transaction_lock():
            if not self.audit_journal_integrity():
                raise BoundaryEscapeViolation("Journal corrupto durante recovery")
            committed_tokens = set()
            rolled_back_tokens = set()
            prepared_tokens = set()
            latest_committed_target = {}
            begun_tokens = {}
            with open(self.journal_path, "r") as j:
                for index, line in enumerate(j):
                    parts = line.strip().split()
                    action, tok, p_hash, encoded_name, prior_state = parts[2], parts[3], parts[4], parts[6], parts[7]
                    filename = bytes.fromhex(encoded_name).decode("utf-8") if encoded_name != "-" else ""
                    if action == "BEGIN":
                        begun_tokens[tok] = (p_hash, filename, prior_state, index)
                    elif action == "PREPARED":
                        prepared_tokens.add(tok)
                    elif action == "COMMIT":
                        committed_tokens.add(tok)
                        latest_committed_target[filename] = index
                    elif action == "ROLLBACK":
                        rolled_back_tokens.add(tok)

            for tok, (p_hash, filename, prior_state, begin_index) in begun_tokens.items():
                backup_path = os.path.join(self.vault_dir, f".bak_{tok}")
                temp_path = os.path.join(self.vault_dir, f".tmp_{tok}")
                if (
                    tok in committed_tokens
                    or tok in rolled_back_tokens
                    or latest_committed_target.get(filename, -1) > begin_index
                ):
                    if os.path.lexists(backup_path):
                        os.remove(backup_path)
                        self._sync_parent_dir(backup_path)
                    if os.path.lexists(temp_path):
                        os.remove(temp_path)
                        self._sync_parent_dir(temp_path)
                    continue
                fpath = os.path.join(self.vault_dir, filename)
                if tok in prepared_tokens:
                    if prior_state == "EXISTED":
                        try:
                            fd = os.open(backup_path, os.O_RDONLY | os.O_NOFOLLOW)
                        except OSError as exc:
                            raise BoundaryEscapeViolation(f"Respaldo ausente para {tok}") from exc
                        try:
                            if not stat.S_ISREG(os.fstat(fd).st_mode):
                                raise BoundaryEscapeViolation(f"Respaldo inválido para {tok}")
                        finally:
                            os.close(fd)
                        os.replace(backup_path, fpath)
                        self._sync_parent_dir(fpath)
                    elif prior_state == "ABSENT":
                        try:
                            fd = os.open(fpath, os.O_RDONLY | os.O_NOFOLLOW)
                        except FileNotFoundError:
                            fd = None
                        except OSError as exc:
                            raise BoundaryEscapeViolation(f"Destino inválido para {tok}") from exc
                        if fd is not None:
                            with os.fdopen(fd, "rb") as f:
                                if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                                    raise BoundaryEscapeViolation(f"Destino inválido para {tok}")
                                if hashlib.sha256(f.read()).hexdigest() != p_hash:
                                    raise BoundaryEscapeViolation(f"Destino modificado para {tok}")
                            os.remove(fpath)
                            self._sync_parent_dir(fpath)
                    else:
                        raise BoundaryEscapeViolation(f"Estado previo inválido para {tok}")
                elif os.path.lexists(backup_path):
                    os.remove(backup_path)
                    self._sync_parent_dir(backup_path)
                if os.path.lexists(temp_path):
                    os.remove(temp_path)
                    self._sync_parent_dir(temp_path)
                self.append_journal_block("ROLLBACK", tok, p_hash, filename)


def run_fl016():
    print("=================================================================")
    print("   EXPERIMENTO FL-016: ADVERSARIAL BOUNDARY ESCAPE (E5 - macOS)")
    print("=================================================================")

    with tempfile.TemporaryDirectory() as raw_base_dir:
        base_dir = os.path.realpath(raw_base_dir)
        vault_dir = os.path.join(base_dir, "broker_vault")
        os.makedirs(vault_dir, exist_ok=True)
        journal_file = os.path.join(base_dir, "broker_chain.journal")

        broker = E5BrokerKernel(vault_dir, journal_file)

        # [A1] Escritura Directa al Almacén
        print("\n[A1] Ataque de Escritura Directa al Almacén Protegido:")
        os.chmod(vault_dir, 0o500)
        try:
            with open(os.path.join(vault_dir, "unauthorized_direct.txt"), "w") as f:
                f.write("bypass")
            print("  ❌ FAIL: El archivo pudo escribirse directamente.")
            sys.exit(1)
        except OSError as e:
            if e.errno in (errno.EACCES, errno.EPERM):
                print(f"  ✅ PASS: Veto coercitivo del SO ({e.strerror}) ante bypass directo.")
            else:
                raise
        finally:
            os.chmod(vault_dir, 0o700)

        # [A2] Symlink en Componente Intermedio
        print("\n[A2] Inyección de Symlink en Carpeta Intermedia del Vault:")
        sub_dir = os.path.join(vault_dir, "sub_real")
        os.makedirs(sub_dir, exist_ok=True)
        symlink_dir = os.path.join(vault_dir, "sub_symlink")
        os.symlink(sub_dir, symlink_dir)

        evil_path = os.path.join(symlink_dir, "target.txt")
        try:
            broker.verify_no_symlink_in_jail(evil_path)
            print("  ❌ FAIL: La comprobación de ruta aceptó un symlink en subcarpeta.")
            sys.exit(1)
        except BoundaryEscapeViolation as e:
            print(f"  ✅ PASS: {e}")
        assert broker.execute_mediated_effect("tok_escape", "../broker_vault_sibling/escaped.txt", b"breach") is False
        assert not os.path.exists(os.path.join(base_dir, "broker_vault_sibling", "escaped.txt"))

        # [A3] Doble Consumo Concurrente
        print("\n[A3] Intento Concurrente de Doble Consumo (Mismo Token en 2 Hilos):")
        tok_id = "tok_concurrente_001"
        results = []

        def racer(idx):
            res = broker.execute_mediated_effect(tok_id, f"output_{idx}.txt", f"data_{idx}".encode())
            results.append(res)

        with ThreadPoolExecutor(max_workers=2) as executor:
            t1 = executor.submit(racer, 1)
            t2 = executor.submit(racer, 2)
            t1.result()
            t2.result()

        success_count = sum(1 for r in results if r is True)
        assert success_count == 1, f"BRECHA: {success_count} commits autorizados para el mismo token"
        print(f"  ✅ PASS: Exactamente 1 commit autorizado ({success_count}/2). Anti-Replay verificado.")

        # [A4] Crash entre Efecto y ACK
        print("\n[A4] Crash Inyectado tras Efecto sin ACK (Recuperación Transaccional):")
        tok_crash = "tok_crash_orphan"
        broker.execute_mediated_effect(tok_crash, "orphan.txt", b"uncommitted_data", inject_crash_after_effect=True)
        assert os.path.exists(os.path.join(vault_dir, "orphan.txt")), "Setup error"

        broker = E5BrokerKernel(vault_dir, journal_file)
        broker.recovery_protocol()
        assert not os.path.exists(os.path.join(vault_dir, "orphan.txt")), "BRECHA: Archivo huérfano sobrevivió"
        assert broker.execute_mediated_effect("tok_valid_same", "valid_same.txt", b"same_payload")
        broker.execute_mediated_effect(
            "tok_orphan_same", "orphan_same.txt", b"same_payload", inject_crash_after_effect=True
        )
        broker.recovery_protocol()
        assert os.path.exists(os.path.join(vault_dir, "valid_same.txt")), "BRECHA: Recovery borró un archivo confirmado"
        assert not os.path.exists(os.path.join(vault_dir, "orphan_same.txt")), (
            "BRECHA: Recovery conservó un archivo huérfano"
        )
        assert broker.execute_mediated_effect("tok_original", "overwrite.txt", b"original")
        assert not broker.execute_mediated_effect(
            "tok_overwrite_crash", "overwrite.txt", b"replacement", inject_crash_after_effect=True
        )
        assert Path(vault_dir, "overwrite.txt").read_bytes() == b"replacement"
        broker = E5BrokerKernel(vault_dir, journal_file)
        broker.recovery_protocol()
        assert Path(vault_dir, "overwrite.txt").read_bytes() == b"original", "BRECHA: Overwrite no revertido"
        assert not os.path.exists(os.path.join(vault_dir, ".bak_tok_overwrite_crash"))
        assert not broker.execute_mediated_effect("tok_overwrite_crash", "replayed.txt", b"replay")
        assert broker.execute_mediated_effect("tok_later_original", "later.txt", b"original")
        assert not broker.execute_mediated_effect(
            "tok_later_crash", "later.txt", b"intermediate", inject_crash_after_effect=True
        )
        assert broker.execute_mediated_effect("tok_later_commit", "later.txt", b"final")
        broker = E5BrokerKernel(vault_dir, journal_file)
        broker.recovery_protocol()
        assert Path(vault_dir, "later.txt").read_bytes() == b"final"
        assert not os.path.exists(os.path.join(vault_dir, ".bak_tok_later_crash"))
        assert broker.audit_journal_integrity()
        print("  ✅ PASS: Archivo huérfano revertido atómicamente tras crash.")

        # [A5] Revocación en el Punto de Linearización
        print("\n[A5] Revocación Concurrente Previa a Mutación:")
        tok_rev = "tok_linearization_test"
        broker.revoke_token(tok_rev)
        executed = broker.execute_mediated_effect(tok_rev, "should_fail.txt", b"forbidden")
        assert executed is False
        assert not os.path.exists(os.path.join(vault_dir, "should_fail.txt"))
        print("  ✅ PASS: Linearización estricta: token revocado genera 0 efectos en disco.")

        # [A6] Manipulación del Journal
        print("\n[A6] Auditoría de Integridad y Detección de Alteración en Journal:")
        assert broker.audit_journal_integrity() is True
        print("  ├─ Hash chain íntegra verificada.")
        with open(journal_file, "r+") as j:
            content = j.read()
            j.seek(0)
            j.write(content.replace("COMMIT", "COMMIX"))
        assert broker.audit_journal_integrity() is False
        print("  ✅ PASS: Alteración de journal detectada por rotura de cadena SHA-256.")
        try:
            broker.execute_mediated_effect("tok_tampered", "tampered.txt", b"forbidden")
            raise AssertionError("BRECHA: El journal corrupto permitió un efecto")
        except BoundaryEscapeViolation:
            assert not os.path.exists(os.path.join(vault_dir, "tampered.txt"))

    print("\n-----------------------------------------------------------------")
    print("VEREDICTO FL-016: ✅ 6/6 CASOS LOCALES SUPERADOS")
    print("ALCANCE: archivos temporales y brokers cooperantes con journal compartido.")
    print("El confinamiento de un agente adversarial requiere una campaña independiente.")
    print("-----------------------------------------------------------------")


if __name__ == "__main__":
    run_fl016()
