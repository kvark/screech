//! Locate the pinned Blade shader sources for the browser's embedded VFS.
fn main() {
    println!("cargo:rerun-if-changed=Cargo.toml");
    println!("cargo:rerun-if-changed=Cargo.lock");
    if std::env::var("CARGO_CFG_TARGET_ARCH").as_deref() != Ok("wasm32") {
        return;
    }
    let output = std::process::Command::new(std::env::var("CARGO").expect("CARGO"))
        .args([
            "metadata",
            "--format-version=1",
            "--locked",
            "--filter-platform=wasm32-unknown-unknown",
        ])
        .current_dir(std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"))
        .output()
        .expect("unable to run cargo metadata");
    assert!(
        output.status.success(),
        "cargo metadata failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let metadata: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("cargo metadata JSON");
    let package = metadata["packages"]
        .as_array()
        .expect("packages")
        .iter()
        .find(|p| p["name"] == "blade-render")
        .expect("blade-render package");
    let shaders = std::path::Path::new(package["manifest_path"].as_str().expect("manifest_path"))
        .parent()
        .expect("blade-render directory")
        .join("code");
    assert!(
        shaders.join("raster.wgsl").is_file(),
        "Blade raster shader missing"
    );
    println!(
        "cargo:rustc-env=SCREECH_BLADE_SHADER_DIR={}",
        shaders.display()
    );
    println!("cargo:rerun-if-changed={}", shaders.display());
    println!("cargo:rerun-if-changed=data");
}
