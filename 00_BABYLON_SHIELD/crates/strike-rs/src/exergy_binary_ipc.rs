use ciborium::Value;
use sha3::{Digest, Sha3_256};
use std::collections::BTreeMap;
use anyhow::{Result, bail};

pub const MAGIC_HEADER: &[u8; 6] = b"B60IPC";
pub const VERSION: u8 = 1;
pub const HEADER_SIZE: usize = 23;

#[derive(Debug, Clone)]
pub struct ExergyPacket {
    pub sender: String,
    pub recipient: String,
    pub payload: BTreeMap<String, Value>,
    pub lamport_t: u64,
}

impl ExergyPacket {
    pub fn pack(&self) -> Result<Vec<u8>> {
        let mut payload_raw = Vec::new();
        ciborium::into_writer(&self.payload, &mut payload_raw)?;
        
        let sender_bytes = self.sender.as_bytes();
        let recipient_bytes = self.recipient.as_bytes();
        
        let mut header = Vec::with_capacity(HEADER_SIZE);
        header.extend_from_slice(MAGIC_HEADER);
        header.push(VERSION);
        header.extend_from_slice(&(sender_bytes.len() as u16).to_be_bytes());
        header.extend_from_slice(&(recipient_bytes.len() as u16).to_be_bytes());
        header.extend_from_slice(&self.lamport_t.to_be_bytes());
        header.extend_from_slice(&(payload_raw.len() as u32).to_be_bytes());
        
        let mut body = Vec::with_capacity(sender_bytes.len() + recipient_bytes.len() + payload_raw.len());
        body.extend_from_slice(sender_bytes);
        body.extend_from_slice(recipient_bytes);
        body.extend_from_slice(&payload_raw);
        
        let mut hasher = Sha3_256::new();
        hasher.update(&header);
        hasher.update(&body);
        let checksum = &hasher.finalize()[..8];
        
        let mut packet = Vec::with_capacity(header.len() + body.len() + 8);
        packet.extend_from_slice(&header);
        packet.extend_from_slice(&body);
        packet.extend_from_slice(checksum);
        
        Ok(packet)
    }

    pub fn unpack(raw_bytes: &[u8]) -> Result<Self> {
        if raw_bytes.len() < HEADER_SIZE + 8 {
            bail!("Longitud binaria insuficiente para cabecera B60IPC");
        }
        
        let magic = &raw_bytes[0..6];
        if magic != MAGIC_HEADER {
            bail!("Cabecera magica invalida para B60IPC");
        }
        
        let version = raw_bytes[6];
        if version != VERSION {
            bail!("Version B60IPC no soportada");
        }
        
        let mut cursor = 7;
        let sender_len = u16::from_be_bytes(raw_bytes[cursor..cursor+2].try_into().map_err(|_| anyhow::anyhow!("B60IPC slice bounds violation"))?) as usize;
        cursor += 2;
        let recipient_len = u16::from_be_bytes(raw_bytes[cursor..cursor+2].try_into().map_err(|_| anyhow::anyhow!("B60IPC slice bounds violation"))?) as usize;
        cursor += 2;
        let lamport_t = u64::from_be_bytes(raw_bytes[cursor..cursor+8].try_into().map_err(|_| anyhow::anyhow!("B60IPC slice bounds violation"))?);
        cursor += 8;
        let payload_len = u32::from_be_bytes(raw_bytes[cursor..cursor+4].try_into().map_err(|_| anyhow::anyhow!("B60IPC slice bounds violation"))?) as usize;
        // cursor += 4; // cursor should be 23 now (HEADER_SIZE)
        
        let expected_total = HEADER_SIZE + sender_len + recipient_len + payload_len + 8;
        if raw_bytes.len() != expected_total {
            bail!("Integridad de payload de mensaje binario comprometida");
        }
        
        let body_start = HEADER_SIZE;
        let body_end = body_start + sender_len + recipient_len + payload_len;
        
        let checksum_actual = &raw_bytes[body_end..body_end+8];
        
        let mut hasher = Sha3_256::new();
        hasher.update(&raw_bytes[..body_end]);
        let computed = &hasher.finalize()[..8];
        
        if checksum_actual != computed {
            bail!("Checksum SHA3-256 invalido en mensaje inter-agente");
        }
        
        let sender_bytes = &raw_bytes[body_start..body_start+sender_len];
        let recipient_bytes = &raw_bytes[body_start+sender_len..body_start+sender_len+recipient_len];
        let payload_raw = &raw_bytes[body_start+sender_len+recipient_len..body_end];
        
        let sender = String::from_utf8(sender_bytes.to_vec())?;
        let recipient = String::from_utf8(recipient_bytes.to_vec())?;
        
        let payload: BTreeMap<String, Value> = ciborium::from_reader(payload_raw)?;
        
        Ok(Self {
            sender,
            recipient,
            payload,
            lamport_t,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;
    use ciborium::Value;

    #[test]
    fn test_exergy_binary_ipc_pack_unpack() {
        let mut payload = BTreeMap::new();
        payload.insert("command".to_string(), Value::Text("deploy".to_string()));
        payload.insert("exergy".to_string(), Value::Integer(42.into()));

        let packet = ExergyPacket {
            sender: "agent_alpha".to_string(),
            recipient: "agent_omega".to_string(),
            payload,
            lamport_t: 1337,
        };

        let raw = packet.pack().unwrap();
        let unpacked = ExergyPacket::unpack(&raw).unwrap();

        assert_eq!(unpacked.sender, "agent_alpha");
        assert_eq!(unpacked.recipient, "agent_omega");
        assert_eq!(unpacked.lamport_t, 1337);
        assert_eq!(
            unpacked.payload.get("command").unwrap(),
            &Value::Text("deploy".to_string())
        );
    }
}
