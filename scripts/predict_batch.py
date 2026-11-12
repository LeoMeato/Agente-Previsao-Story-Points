#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Encaminhador para predict_batch.py na raiz do repositório.
Permite executar: python scripts/predict_batch.py -n 5 ...
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from predict_batch import main

if __name__ == "__main__":
    main()
