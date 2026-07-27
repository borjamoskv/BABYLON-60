use grammers_client::{Client, SenderPool};
use grammers_session::storages::SqliteSession;
use std::sync::Arc;
use std::io::{self, Write};
use dotenv::dotenv;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenv().ok();

    let api_id: i32 = std::env::var("TG_API_ID")
        .expect("TG_API_ID must be set")
        .parse()?;
    let api_hash = std::env::var("TG_API_HASH").expect("TG_API_HASH must be set");

    println!(">>> [OUROBOROS-AUTH] Iniciando flujo de autenticación Telegram...");

    let session = Arc::new(SqliteSession::open("ouroboros.session").await?);
    let pool = SenderPool::new(Arc::clone(&session), api_id);
    let client = Client::new(pool.handle);

    tokio::spawn(pool.runner.run());

    if client.is_authorized().await? {
        println!(">>> [OUROBOROS-AUTH] YA ESTÁS AUTORIZADO. Sesión guardada en 'ouroboros.session'.");
        return Ok(());
    }

    println!("Introduce tu número de teléfono (formato internacional, ej: +34...):");
    let mut phone = String::new();
    io::stdin().read_line(&mut phone)?;
    let phone = phone.trim().to_string();

    let login_token = client.request_login_code(&phone, &api_hash).await?;

    print!("Introduce el código recibido por Telegram: ");
    io::stdout().flush()?;
    let mut code = String::new();
    io::stdin().read_line(&mut code)?;
    let code = code.trim().to_string();

    match client.sign_in(&login_token, &code).await {
        Ok(_) => {
            println!(">>> [OUROBOROS-AUTH] ÉXITO. Autenticación completada.");
            println!("La sesión se ha guardado en 'ouroboros.session'.");
            println!("Ya puedes ejecutar el bindeo principal con 'cargo run --release'.");
        }
        Err(e) => {
            println!(">>> [OUROBOROS-AUTH] ERROR: {:?}", e);
            println!("Si tienes 2FA activado, se requiere el intercambio del password (flujo extendido).");
        }
    }

    Ok(())
}
