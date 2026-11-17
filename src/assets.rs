use std::{io, path::Path};

/// Browser assets are mounted before the engine starts. Native keeps its normal
/// filesystem path, while generated/in-memory Blade assets work on both targets.
pub fn read(path: &Path) -> io::Result<Vec<u8>> {
    if let Some(bytes) = blade_engine::vfs::read(path) {
        return Ok(bytes);
    }
    #[cfg(not(target_arch = "wasm32"))]
    {
        std::fs::read(path)
    }
    #[cfg(target_arch = "wasm32")]
    {
        Err(io::Error::new(
            io::ErrorKind::NotFound,
            format!("asset is not embedded: {}", path.display()),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_virtual_files() {
        let path = Path::new("/screech-test/embedded.txt");
        blade_engine::vfs::mount(path, b"embedded".to_vec());
        assert_eq!(read(path).unwrap(), b"embedded");
    }

    #[test]
    fn native_configs_remain_readable() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("data");
        let _: crate::config::Level =
            ron::de::from_bytes(&read(&root.join("level.ron")).unwrap()).unwrap();
        let _: crate::config::Vehicle =
            ron::de::from_bytes(&read(&root.join("raceFuture.ron")).unwrap()).unwrap();
    }

    #[test]
    fn missing_asset_reports_not_found() {
        assert_eq!(
            read(Path::new("data/nonexistent-screech-test"))
                .unwrap_err()
                .kind(),
            io::ErrorKind::NotFound
        );
    }
}
