use std::process::Command;

use cursive::Cursive;
use cursive::views::{Dialog};

struct Task {
    name: &'static str,
    
}

impl Task {
    fn execute(&self, s: &mut Cursive) {
                
    }

    fn execute_test(&self) {
        // let output = Command::new("echo Testing ");
    }
}

static DOCKER_COMPOSE_STOP: Task = Task {
    name: "Detener servidor de Docker (docker-compose)"
};

