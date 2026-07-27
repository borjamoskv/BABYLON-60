// C5-REAL EXERGY CERTIFIED
// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    babylon_mail_lib::run();
}
