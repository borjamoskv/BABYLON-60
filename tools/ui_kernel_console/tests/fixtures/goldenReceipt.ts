// Generado por tests/fixtures/writeGolden.ts. No editar a mano.

/** Semilla Ed25519 de prueba: este byte repetido 32 veces (la misma que usan los vectores ACS del kernel). */
export const GOLDEN_SEED_BYTE = "11";

export const GOLDEN_POLICY = {
  "admitted_authorities": [
    "0xd04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737" // pragma: allowlist secret
  ],
  "larsa_required_weight": 4
};

/** Recibo tal como viaja en JSON. */
export const GOLDEN_RECEIPT = {
  "execution_id": "b60-exec-01931a7c-8f00-7000-8000-000000000060",
  "manifest_version": "v5.1.0",
  "causal_clock": {
    "policy_epoch": 51,
    "logical_tick": 1048,
    "seq_id": 4096
  },
  "ingress": {
    "agent_id": "agent://cortex/rea-auditor-01",
    "policy_profile": "NEMESIS_ADVERSARIAL",
    "payload_raw": "{\"op\":\"fs.write\",\"target\":\"/etc/hosts\",\"pre_seal\":false}"
  },
  "execution_dag": [
    {
      "node_id": "EV_00001048_000000",
      "parent_ids": [],
      "state_status": "COMMITTED",
      "smt_verified": true,
      "reduction_steps": 14,
      "state_hash": "0x847730be351fbc8103628e6025da82a0ea251a0b750d5f822fe167247235581f", // pragma: allowlist secret
      "violation_reason": null
    },
    {
      "node_id": "EV_00001048_000001",
      "parent_ids": [
        "EV_00001048_000000"
      ],
      "state_status": "COMMITTED",
      "smt_verified": true,
      "reduction_steps": 82,
      "state_hash": "0x9dd4c56d646d62297597a6708d0818185a72e109550debfff905e773f963f424", // pragma: allowlist secret
      "violation_reason": null
    },
    {
      "node_id": "EV_00001048_000002",
      "parent_ids": [
        "EV_00001048_000000"
      ],
      "state_status": "INTERCEPTED_NEMESIS",
      "smt_verified": true,
      "reduction_steps": 19,
      "state_hash": "0x93edb42ff7ec13f3d9df9d0cac7a5cac37d589c606f2ded5b62a69f9897a0f48", // pragma: allowlist secret
      "violation_reason": "INV_C5_FLASH_DEFENSE: Side-Effect Without Pre-Seal"
    },
    {
      "node_id": "EV_00001048_000003",
      "parent_ids": [
        "EV_00001048_000001"
      ],
      "state_status": "COMMITTED",
      "smt_verified": true,
      "reduction_steps": 31,
      "state_hash": "0xbc427abfeeed613e85d73676eca73e3b5f5a339ed000c131694059b51f928cf6", // pragma: allowlist secret
      "violation_reason": null
    }
  ],
  "cryptographic_seal": {
    "phase_one_manifest_hash": "0xa1496b0fdea481230b444f1ce8d444db0539b33f5647ffc5bfe50ae23fd96cd1", // pragma: allowlist secret
    "phase_two_merkle_root": "b3:dcc09ce920bdf04a6c366aedff3bceb325dbbab7808b188c078a21bd7b9981fd", // pragma: allowlist secret
    "ed25519_public_key": "0xd04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737", // pragma: allowlist secret
    "ed25519_signature": "0x796160aa7b0c09d16887856248fb0529d81cd1659fa11f89691b830b420f1ac972020bf12c0520a22b0ab15f8eb1020e82436236479823c2a86ae5d082224e07", // pragma: allowlist secret
    "larsa_commit": {
      "trace_hash": "0x071324b2530edf9d13ca08684e83f7c27f92013d57437e5bbc7c1f35ef3c9f60", // pragma: allowlist secret
      "heuristic_weight": 5
    },
    "lean4_proof": {
      "status": "VERIFIED_NO_SORRY",
      "theorem_ident": "Fixture.Synthetic.transition_soundness",
      "sorry_count": 0
    }
  },
  "audit_metrics": {
    "memory_bytes": 16384,
    "prev_receipt_hash": "0xb484ab032e076abbfb27b4a883eeda4cd42a210f5750d6c9ff0a4b898a820eb5", // pragma: allowlist secret
    "worm_txid": "0x13940f339898d7673f4cde4054bdd632e66dd8099a4a4173b1f88890e335b66f" // pragma: allowlist secret
  }
};

/** Bytes intermedios en hex: preimagen de cada nodo, manifiesto, sobre y entrada de la firma. */
export const GOLDEN_INTERMEDIATE = {
  "node_preimages": {
    "EV_00001048_000000": "8776424142594c4f4e36305f455845435f4e4f44455f56317245565f30303030313034385f3030303030308069434f4d4d4954544544010e80", // pragma: allowlist secret
    "EV_00001048_000001": "8776424142594c4f4e36305f455845435f4e4f44455f56317245565f30303030313034385f303030303031817245565f30303030313034385f30303030303069434f4d4d495454454401185280", // pragma: allowlist secret
    "EV_00001048_000002": "8776424142594c4f4e36305f455845435f4e4f44455f56317245565f30303030313034385f303030303032817245565f30303030313034385f30303030303073494e5445524345505445445f4e454d455349530113817832494e565f43355f464c4153485f444546454e53453a20536964652d45666665637420576974686f7574205072652d5365616c", // pragma: allowlist secret
    "EV_00001048_000003": "8776424142594c4f4e36305f455845435f4e4f44455f56317245565f30303030313034385f303030303033817245565f30303030313034385f30303030303169434f4d4d495454454401181f80" // pragma: allowlist secret
  },
  "manifest_preimage": "89781a424142594c4f4e36305f455845435f4d414e49464553545f5631782d6236302d657865632d30313933316137632d386630302d373030302d383030302d3030303030303030303036306676352e312e301833190418191000781d6167656e743a2f2f636f727465782f7265612d61756469746f722d3031734e454d455349535f414456455253415249414c78387b226f70223a2266732e7772697465222c22746172676574223a222f6574632f686f737473222c227072655f7365616c223a66616c73657d", // pragma: allowlist secret
  "envelope": "8f7819424142594c4f4e36305f455845435f524543454950545f5631782d6236302d657865632d30313933316137632d386630302d373030302d383030302d30303030303030303030363018331904181910005820a1496b0fdea481230b444f1ce8d444db0539b33f5647ffc5bfe50ae23fd96cd1784362333a646363303963653932306264663034613663333636616564666633626365623332356462626162373830386231383863303738613231626437623939383166645820071324b2530edf9d13ca08684e83f7c27f92013d57437e5bbc7c1f35ef3c9f60057156455249464945445f4e4f5f534f5252597826466978747572652e53796e7468657469632e7472616e736974696f6e5f736f756e646e657373001940005820b484ab032e076abbfb27b4a883eeda4cd42a210f5750d6c9ff0a4b898a820eb5582013940f339898d7673f4cde4054bdd632e66dd8099a4a4173b1f88890e335b66f", // pragma: allowlist secret
  "signature_input": "846a5369676e61747572653143a101274059015f8f7819424142594c4f4e36305f455845435f524543454950545f5631782d6236302d657865632d30313933316137632d386630302d373030302d383030302d30303030303030303030363018331904181910005820a1496b0fdea481230b444f1ce8d444db0539b33f5647ffc5bfe50ae23fd96cd1784362333a646363303963653932306264663034613663333636616564666633626365623332356462626162373830386231383863303738613231626437623939383166645820071324b2530edf9d13ca08684e83f7c27f92013d57437e5bbc7c1f35ef3c9f60057156455249464945445f4e4f5f534f5252597826466978747572652e53796e7468657469632e7472616e736974696f6e5f736f756e646e657373001940005820b484ab032e076abbfb27b4a883eeda4cd42a210f5750d6c9ff0a4b898a820eb5582013940f339898d7673f4cde4054bdd632e66dd8099a4a4173b1f88890e335b66f", // pragma: allowlist secret
  "receipt_hash": "0x5a8abc8352a4020737612a8114ba4fb429f84ef37fe760b615e16fed2d05b3c5" // pragma: allowlist secret
};
