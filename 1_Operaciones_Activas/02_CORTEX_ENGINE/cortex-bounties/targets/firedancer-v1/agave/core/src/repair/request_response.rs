// C5-REAL EXERGY CERTIFIED
pub trait RequestResponse {
    type Response: ?Sized;
    fn num_expected_responses(&self) -> u32;
    fn verify_response(&self, response: &Self::Response) -> bool;
}
