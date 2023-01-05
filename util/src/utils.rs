use std::io;
use std::io::prelude::*;

use cursive::Cursive;
use cursive::view::IntoBoxedView;
use cursive::views::{Dialog};

pub fn new_task(s: &mut Cursive, task: &dyn Fn() -> Dialog) {
    s.pop_layer();
    let task_view = task();
    s.add_layer(task_view);
}

pub fn gen_dialog<V: IntoBoxedView>(title: String, view: V) -> Dialog {
    Dialog::around(view)
        .title(title)
}

pub fn pause() {
    let mut stdin = io::stdin();
    let mut stdout = io::stdout();

    write!(stdout, "Press any key...").unwrap();
    stdout.flush().unwrap();

    let _ = stdin.read(&mut [0u8]).unwrap();

}

