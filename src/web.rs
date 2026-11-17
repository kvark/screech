use include_dir::{Dir, include_dir};
use wasm_bindgen::JsCast as _;
use winit::platform::web::{WindowAttributesExtWebSys as _, WindowExtWebSys as _};

pub fn initialize() {
    console_error_panic_hook::set_once();
    let _ = console_log::init_with_level(log::Level::Info);
    static DATA: Dir = include_dir!("$CARGO_MANIFEST_DIR/data");
    static SHADERS: Dir = include_dir!("$SCREECH_BLADE_SHADER_DIR");
    fn mount(dir: &Dir, root: &std::path::Path) {
        for file in dir.files() {
            blade_engine::vfs::mount(root.join(file.path()), file.contents().to_vec());
        }
        for child in dir.dirs() {
            mount(child, root);
        }
    }
    mount(
        &DATA,
        &std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("data"),
    );
    mount(&SHADERS, &blade_render::shader_dir());
}

pub fn window_attributes(
    attributes: winit::window::WindowAttributes,
) -> winit::window::WindowAttributes {
    let canvas = web_sys::window()
        .and_then(|w| w.document())
        .and_then(|d| d.get_element_by_id(blade_graphics::CANVAS_ID))
        .expect("web shell must contain the Blade canvas")
        .dyn_into::<web_sys::HtmlCanvasElement>()
        .expect("Blade canvas element");
    attributes
        .with_canvas(Some(canvas))
        .with_prevent_default(true)
}

/// CSS dimensions and the WebGL drawing buffer are independent. Keep device
/// pixels in sync on resize/scale changes, without clearing the canvas every frame.
pub fn sync_canvas(window: &winit::window::Window) {
    let canvas = window.canvas().expect("winit canvas");
    let size = window.inner_size();
    if canvas.width() != size.width.max(1) {
        canvas.set_width(size.width.max(1));
    }
    if canvas.height() != size.height.max(1) {
        canvas.set_height(size.height.max(1));
    }
}

pub fn dispatch(name: &str) {
    if let Some(window) = web_sys::window() {
        let _ = window.dispatch_event(&web_sys::Event::new(name).expect("web event"));
    }
}
