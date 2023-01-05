use cursive::{Cursive, CursiveExt};
use cursive::align::VAlign;
use cursive::views::{Dialog, TextView, SelectView, BoxedView};

mod utils;
mod tasks;

fn main() {
    let mut task_select = SelectView::new();
    task_select.add_item("Create new module", 1);

    task_select.set_on_submit(|s, task| {
        s.pop_layer();
        s.add_fullscreen_layer(BoxedView::boxed(TextView::new("XD")
                                                .v_align(VAlign::Bottom)));
    });

    let task_dialog = Dialog::around(task_select)
        .title("ODOO utilitiy");

    let mut siv = Cursive::new();
    siv.add_layer(task_dialog);

    siv.add_global_callback('q', |s| s.quit());

    siv.run();
    println!("Stopped");
}

