import os
import shutil
import zipfile
import json
import tkinter as tk
from tkinter import filedialog, messagebox
"""
流程：
打开用户指定路劲并找到mods文件夹（没有则通过messagebox提示用户并退出）和resourcepacks文件夹（如果没有则给出提示并继续程序），
遍历其中的jar文件并以压缩包的形式打开，获取其中的assets文件夹（如果没有则跳过），
获取assets中除了minecraft文件夹的其它文件夹（也就是其它命名空间），遍历这些文件夹查看内部是否存在lang文件夹，
如果有则把命名空间这个文件夹和内部的lang文件夹（和lang同级的其它文件和文件夹则舍弃）复制到resourcepacks文件夹下创建的I18N文件夹的创建的"原文"文件夹中。
然后遍历resourcepacks文件夹查看是否存在Minecraft-Mod-Language开头的zip文件，有多个则给出ui让用户选择，没有就给出提示并结束程序，
接着提取这个zip并打开assets文件夹，把这些命名空间的文件夹解压到resourcepacks文件夹下创建的I18N文件夹的创建的"i18n模组汉化"文件夹中，
对比原文和i18n模组汉化两个文件夹下的各个命名空间的lang文件夹，
如果原文命名空间在i18n模组汉化中不存在，则将此命名空间的文件夹复制到resourcepacks文件夹下创建的I18N文件夹的创建的"未翻译"文件夹中，
如果命名空间存在在i18n模组汉化中，且命名空间内lang文件夹内不包含zh_cn.json，则对比原文的命名空间的lang文件夹中en_us.json（如果不存在则遍历选取第一个json文件）的
和i18n模组汉化的命名空间的lang文件夹中的zh_cn.json的各个键字，
如果有键子在i18n模组汉化的json中不存在，则复制原文的键值对到i18n模组汉化的命名空间的lang文件夹中的zh_cn.json中
再将此命名空间复制到resourcepacks文件夹下I18N文件夹的"未翻译"文件夹中。
"""
def main():
    # 创建Tkinter主窗口并隐藏
    root = tk.Tk()
    root.withdraw()
    
    # 让用户选择目录
    user_path = filedialog.askdirectory(title="选择Minecraft根目录")
    if not user_path:
        messagebox.showerror("错误", "未选择目录，程序退出。")
        return

    mods_path = os.path.join(user_path, "mods")
    resourcepacks_path = os.path.join(user_path, "resourcepacks")

    if not os.path.exists(mods_path):
        messagebox.showerror("错误", "未找到mods文件夹，程序退出。")
        return

    if not os.path.exists(resourcepacks_path):
        messagebox.showwarning("警告", "未找到resourcepacks文件夹，程序继续。")
        os.makedirs(resourcepacks_path)

    # 创建I18N目录结构
    i18n_path = os.path.join(resourcepacks_path, "I18N")
    original_path = os.path.join(i18n_path, "原文")
    translated_path = os.path.join(i18n_path, "i18n模组汉化")
    untranslated_path = os.path.join(i18n_path, "未翻译")
    os.makedirs(original_path, exist_ok=True)
    os.makedirs(translated_path, exist_ok=True)
    os.makedirs(untranslated_path, exist_ok=True)

    # 处理mods文件夹中的jar文件
    for file_name in os.listdir(mods_path):
        if file_name.endswith(".jar"):
            jar_path = os.path.join(mods_path, file_name)
            with zipfile.ZipFile(jar_path, 'r') as jar_file:
                if 'assets/' in jar_file.namelist():
                    for asset in jar_file.namelist():
                        if asset.startswith('assets/') and not asset.startswith('assets/minecraft/'):
                            namespace = asset.split('/')[1]
                            if f'assets/{namespace}/lang/' in asset:
                                jar_file.extract(asset, original_path)
                                shutil.copytree(os.path.join(original_path, f'assets/{namespace}'), os.path.join(original_path, namespace), dirs_exist_ok=True)
                                shutil.rmtree(os.path.join(original_path, 'assets'))

    # 处理resourcepacks文件夹中的zip文件
    selected_zip = os.path.join(resourcepacks_path,[f for f in os.listdir(resourcepacks_path) if f.startswith("Minecraft-Mod-Language") and f.endswith(".zip")][0])
    if not selected_zip:
        selected_zip = filedialog.askopenfilename(title="选择一个语言包文件", filetypes=[("Zip文件", "*.zip")], initialdir=resourcepacks_path)

    if not selected_zip:
        messagebox.showerror("错误", "未选择语言包文件，程序退出。")
        return

    with zipfile.ZipFile(selected_zip, 'r') as zip_file:
        # 获取zip文件中所有以'assets/'开头的文件的完整路径
        assets_files = [name for name in zip_file.namelist() if name.startswith('assets/')]

        # 为每个匹配的文件创建目标路径（去除'assets/'前缀）
        for asset_file in assets_files:
            target_path = os.path.join(translated_path, asset_file[len('assets/'):])

            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # 提取文件到目标路径
            with zip_file.open(asset_file) as source, open(target_path, 'wb') as target:
                target.write(source.read())
    
    # 对比原文和i18n模组汉化的lang文件
    for namespace in os.listdir(original_path):
        original_lang_folder = os.path.join(original_path, namespace, "lang")
        if os.path.exists(os.path.join(translated_path, namespace, "lang")):
            original_lang_file = os.path.join(original_path, namespace, "lang", "en_us.json")
            if not os.path.exists(original_lang_file):
                original_lang_file = next((f for f in os.listdir(os.path.join(original_path, namespace, "lang")) if f.endswith(".json")), None)
            translated_lang_file = os.path.join(translated_path, namespace, "lang", "zh_cn.json")
            
            if original_lang_file and os.path.exists(translated_lang_file):
                with open(original_lang_file, 'r', encoding='utf-8') as orig_file, open(translated_lang_file, 'r+', encoding='utf-8') as trans_file:
                    orig_data = json.load(orig_file)
                    trans_data = json.load(trans_file)
                    
                    updated = False
                    for key, value in orig_data.items():
                        if key not in trans_data:
                            trans_data[key] = value
                            updated = True
                    
                    if updated:
                        trans_file.seek(0)
                        json.dump(trans_data, trans_file, ensure_ascii=False, indent=4)
                        trans_file.truncate()
                        shutil.copytree(os.path.join(translated_path, namespace), os.path.join(untranslated_path, namespace), dirs_exist_ok=True)
            else:
                if not os.path.exists(os.path.join(original_lang_folder, "zh_cn.json")):
                    shutil.copytree(original_lang_folder, os.path.join(untranslated_path, namespace, "lang"), dirs_exist_ok=True)
        else:
            if not os.path.exists(os.path.join(original_lang_folder, "zh_cn.json")):
                shutil.copytree(original_lang_folder, os.path.join(untranslated_path, namespace, "lang"), dirs_exist_ok=True)
    messagebox.showinfo("完成", "处理完成。")
if __name__ == "__main__":
    main()
