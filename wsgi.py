#!/usr/bin/env python3
# pylint: disable=invalid-name
from core.startup import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
