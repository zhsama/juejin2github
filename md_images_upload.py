import hashlib
import imghdr
import logging
import os
import re
import shutil
import uuid

import git
import requests


# logging config
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# github username
user_name = "zhsama"

# repo name
github_repository = "juejin2github"

# git repo path
git_repository_folder = "/Users/zhsama/github/juejin2github"

# commit message
commit_message = "chore: add images"

# path for images in git
git_images_folder = git_repository_folder + "/images"

# ignore file/path
ignore_dir_list = [".git"]

# .md file paths(absolute path)
md_file_path = [
    # "/Users/zhsama/github/readme",
]

# UA
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36",
}


def create_name(src):
    """
    generate filename by md5
    :param src:
    :return:
    """
    src_name = src.encode("utf-8")
    s = hashlib.md5()
    s.update(src_name)
    return s.hexdigest()


def get_http_image(image_url):
    """
    get http image
    :param image_url:
    :return:
    """
    file_uuid_name = create_name(image_url)
    image_data = requests.get(image_url, headers=headers).content
    tmp_new_image_path_and_name = os.path.join(git_images_folder, file_uuid_name)
    with open(tmp_new_image_path_and_name, "wb+") as f:
        f.write(image_data)
    img_type = imghdr.what(tmp_new_image_path_and_name)
    if img_type is None:
        img_type = ""
    else:
        img_type = "." + img_type
    # new image path and name
    new_image_path_and_name = tmp_new_image_path_and_name + img_type
    # rename
    os.rename(tmp_new_image_path_and_name, new_image_path_and_name)

    return gen_image_url(new_image_path_and_name, image_url)


def get_local_image(image_url):
    """
    get local image
    :param image_url:
    :return:
    """
    image_info = {"image_url": "", "new_image_url": ""}
    try:
        # uuid filename
        file_uuid_name = uuid.uuid4().hex
        # get image type
        img_type = image_url.split(".")[-1]
        # concat uuid filename and image type
        image_name = file_uuid_name + "." + img_type
        # new image path and name
        new_image_path_and_name = os.path.join(git_images_folder, image_name)
        shutil.copy(image_url, new_image_path_and_name)

        return gen_image_url(new_image_path_and_name, image_url)

    except Exception as e:
        logger.error(e)

    return image_info


def gen_image_url(new_image_path_and_name, image_url):
    """
    generate url
    :param new_image_path_and_name:
    :param image_url:
    :return:
    """
    new_image_url = (
        "https://raw.githubusercontent.com/"
        + user_name
        + "/"
        + github_repository
        + "/main/"
        + git_images_folder.split("/")[-1]
        + "/"
        + new_image_path_and_name.split("/")[-1]
    )
    # image info
    image_info = {"image_url": image_url, "new_image_url": new_image_url}
    logging.info(image_info)
    return image_info


def get_images_from_md_file(md_file):
    """
    get images in .md file
    :param md_file:
    :return:
    """
    image_info_list = []
    with open(md_file, "r+") as f:
        md_content = f.read()
        image_urls = re.findall(r"!\[.*?]\((.*?)\)", md_content)
        for image_url in image_urls:
            # local images
            if not image_url.startswith("http"):
                image_info = get_local_image(image_url)
                image_info_list.append(image_info)
            # net images
            else:
                # ignore svg
                if not image_url.startswith("https://img.shields.io"):
                    try:
                        image_info = get_http_image(image_url)
                        image_info_list.append(image_info)
                    except Exception:
                        logger.error("cannot scrapy :" + image_url)
                        pass
        for image_info in image_info_list:
            md_content = md_content.replace(
                image_info["image_url"], image_info["new_image_url"]
            )

        logger.info("replace completed:", md_content)

        md_content = md_content

    with open(md_file, "w+") as f:
        f.write(md_content)


def git_push_to_origin():
    """
    git push
    :return:
    """
    repo = git.Repo(git_repository_folder)
    logger.info("init success", repo)
    index = repo.index
    index.add(["images/"])
    logger.info("add success")
    index.commit(commit_message)
    logger.info("commit success")
    # 获取远程仓库
    remote = repo.remote()
    logger.info("repo :", remote)
    remote.push()
    logger.info("push success")


def get_md_files(md_dir):
    """
    get all .md files
    :param md_dir:
    :return:
    """
    md_files = []
    for root, dirs, files in sorted(os.walk(md_dir)):
        for file in files:
            # get .md files
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                logger.info(file_path)
                # exclude path/file
                need_append = 0
                for ignore_dir in ignore_dir_list:
                    if ignore_dir in file_path.split("/"):
                        need_append = 1
                if need_append == 0:
                    md_files.append(file_path)
    return md_files


def main():
    if os.path.exists(git_images_folder):
        pass
    else:
        os.mkdir(git_images_folder)
    md_files = []
    for p in md_file_path:
        md_files += get_md_files(p)

    for md_file in md_files:
        get_images_from_md_file(md_file)

    git_push_to_origin()


if __name__ == "__main__":
    main()
