import os
from fastapi.templating import Jinja2Templates


current_dir = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(current_dir, 'templates'))
