import os
import shutil
import tempfile
import dotenv
import pytest


if __name__ == '__main__':
    dotenv.load_dotenv()
    with tempfile.TemporaryDirectory() as tmpdir:
        secrets_dir = os.path.join(tmpdir, 'secrets')
        os.mkdir(secrets_dir)
        for secret in os.listdir("secrets"):
            src = os.path.join("secrets", secret)
            dst = os.path.join(secrets_dir, secret.removesuffix(".secret"))
            shutil.copy(src, dst)
        os.environ['TEST_DB_FILE'] = os.path.join(tmpdir, 'db.sqlite')
        os.environ['SECRETS_DIR'] = secrets_dir
        pytest.main()
