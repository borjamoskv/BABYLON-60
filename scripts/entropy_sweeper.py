import os
import shutil

ROOT_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH_DIR: str = os.path.join(ROOT_DIR, 'scratch')


def sweep() -> None:
    if not os.path.exists(SCRATCH_DIR):
        os.makedirs(SCRATCH_DIR)
        print(f'Created directory: {SCRATCH_DIR}')
    files: list[str] = os.listdir(ROOT_DIR)
    swept_count: int = 0
    for file_name in files:
        if file_name.startswith('scratch_'):
            src_path: str = os.path.join(ROOT_DIR, file_name)
            if os.path.isfile(src_path):
                dest_path: str = os.path.join(SCRATCH_DIR, file_name)
                print(f'Moving: {src_path} -> {dest_path}')
                shutil.move(src_path, dest_path)
                swept_count += 1
    print(f'Sweep complete. Total files swept: {swept_count}')


if __name__ == '__main__':
    sweep()