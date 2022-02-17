import sys
import os
import tempfile
import shutil
import zipfile

from pathlib import Path

def download_from_gdrive(id, destination, file_size=None,
                         model_name='cellpose', progress=None):
    URL = "https://docs.google.com/uc?export=download"
    from requests import Session
    session = Session()

    with session.get(URL, params = { 'id' : id }, stream = True) as response:
        token = get_confirm_token(response)

        if token:
            params = { 'id' : id, 'confirm' : token }
            response = session.get(URL, params = params, stream = True)
        save_response_content(
            response, destination, file_size=file_size, model_name=model_name,
            progress=progress
        )

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination, file_size=None,
                          model_name='cellpose', progress=None):
    print(f'Downloading {model_name} to: {os.path.dirname(destination)}')
    try:
        from tqdm import tqdm
        TQDM_FOUND = True
    except ModuleNotFoundError:
        TQDM_FOUND = False
    CHUNK_SIZE = 32768
    temp_folder = tempfile.mkdtemp()
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)
    temp_dst = os.path.join(temp_folder, os.path.basename(destination))
    if file_size is not None and progress is not None:
        progress.emit(file_size, -1)
    if TQDM_FOUND:
        pbar = tqdm(
            total=file_size, unit='B', unit_scale=True,
            unit_divisor=1024, ncols=100
        )
    else:
        pbar = None
    with open(temp_dst, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                if pbar is not None:
                    pbar.update(len(chunk))
                if progress is not None:
                    progress.emit(-1, len(chunk))
    if pbar is not None:
        pbar.close()

    # Move to destination and delete temp folder
    destination_dir = os.path.dirname(destination)
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    shutil.move(temp_dst, destination)
    shutil.rmtree(temp_folder)

def extract_zip(zip_path, extract_to_path):
    print(f'Extracting to {extract_to_path}...')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to_path)

def get_jdk_info():
    file_id = '1G6SNk5vESqgdxob5UQv87PgVpIJa_dTe'
    file_size = 135524352
    foldername = 'win64'
    jdk_name = 'jdk1.8.0_321'

    acdc_java_path, dot_acdc_java_path = get_acdc_java_path()
    java_path = os.path.join(acdc_java_path, foldername)
    jdk_path = os.path.join(java_path, jdk_name)
    return java_path, jdk_path, file_id, file_size

def download_jdk():
    """Download Java JDK (Windows) to user path ~/.acdc-java"""

    java_path, jdk_path, file_id, file_size = get_jdk_info()
    zip_dst = os.path.join(java_path, 'jdk_temp.zip')

    if os.path.exists(jdk_path):
        return jdk_path

    # Also check the older .acdc-java
    jdk_name = os.path.basename(jdk_path)
    os_foldername = os.path.basename(os.path.dirname(jdk_path))
    _, dot_acdc_java_path = get_acdc_java_path()
    jdk_old_path = os.path.join(dot_acdc_java_path, os_foldername, jdk_name)
    if os.path.exists(jdk_old_path):
        return jdk_old_path

    download_from_gdrive(
        file_id, zip_dst, file_size=file_size, model_name='JDK'
    )
    exctract_to = java_path
    extract_zip(zip_dst, exctract_to)
    # Remove downloaded zip archive
    os.remove(zip_dst)
    print('Java Development Kit downloaded successfully')
    return jdk_path

def get_acdc_java_path():
    user_path = str(Path.home())
    acdc_java_path = os.path.join(user_path, 'acdc-java')
    dot_acdc_java_path = os.path.join(user_path, '.acdc-java')
    return acdc_java_path, dot_acdc_java_path

def get_java_info():
    is_linux = sys.platform.startswith('linux')
    is_mac = sys.platform == 'darwin'
    is_win = sys.platform.startswith("win")
    is_win64 = (is_win and (os.environ["PROCESSOR_ARCHITECTURE"] == "AMD64"))

    # https://drive.google.com/drive/u/0/folders/1MxhySsxB1aBrqb31QmLfVpq8z1vDyLbo
    if is_win64:
        foldername = 'win64'
        jre_name = 'jre1.8.0_301'
        file_id = '1G5zsMusJsB6to_bA-8wT5FHJ6yoS2oCu'
        file_size = 78397719
    elif is_mac:
        foldername = 'macOS'
        jre_name = 'jre1.8.0_301'
        file_id = '1G487QwDlEUJVFLfJkuxvTkFPY_I0XTb8'
        file_size = 108796810
    elif is_linux:
        foldername = 'linux'
        file_id = '1Fz8krhOS8JsX-GhkRDeMiEnAIWqZmCfP'
        jre_name = 'jre1.8.0_301'
        file_size = 92145253
    elif is_win:
        foldername = 'win'
        jre_name = 'jre1.8.0_301'
        return

    acdc_java_path, dot_acdc_java_path = get_acdc_java_path()
    java_path = os.path.join(acdc_java_path, foldername)
    jre_path = os.path.join(java_path, jre_name)
    return java_path, jre_path, file_id, file_size

def download_java():
    """Download Java JRE to user path ~/acdc-java"""

    java_path, jre_path, file_id, file_size = get_java_info()

    zip_dst = os.path.join(java_path, 'java_temp.zip')

    if os.path.exists(jre_path):
        return jre_path

    # Also check the older .acdc-java
    jre_name = os.path.basename(jre_path)
    os_foldername = os.path.basename(os.path.dirname(jre_path))
    _, dot_acdc_java_path = get_acdc_java_path()
    jre_old_path = os.path.join(dot_acdc_java_path, os_foldername, jre_name)
    if os.path.exists(jre_old_path):
        return jre_old_path

    if not os.path.exists(java_path):
        os.makedirs(java_path)

    download_from_gdrive(
        file_id, zip_dst, file_size=file_size, model_name='Java'
    )
    exctract_to = java_path
    extract_zip(zip_dst, exctract_to)
    # Remove downloaded zip archive
    os.remove(zip_dst)
    print('Java downloaded successfully')
    return jre_path

if __name__ == '__main__':
    jre_path = download_java()
    print(jre_path)

    if sys.platform.startswith('win'):
        jdk_path = download_jdk()
        print(jdk_path)
