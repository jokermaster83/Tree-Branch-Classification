FROM python:3.8.19-bookworm


# 替换为USTC的镜像源
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware" >> /etc/apt/sources.list
RUN echo "deb https://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

RUN apt update -y && apt upgrade -y

# 安装 Open3D 系统依赖项和 pip
RUN apt install --no-install-recommends -y \
    libegl1 \
    libgl1 \
    libgomp1 \
    fonts-arphic-ukai \
    fonts-arphic-uming

# 从 PyPI 仓库安装 Open3D
RUN python3 -m pip install --no-cache-dir --upgrade pip

# 代码复制到 Greenplum 文件夹
COPY . /Greenplum

# 设置 Greenplum 文件夹为工作目录
WORKDIR /Greenplum

# 从 requirements.txt 安装依赖项
RUN pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/web/simple

# 安装 uvicorn
RUN pip install uvicorn[standard] -i https://mirrors.ustc.edu.cn/pypi/web/simple

# 添加环境变量
ENV DISPLAY=:0

# 暴露 FastAPI 端口
EXPOSE 23003

# 运行 FastAPI 的命令
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5016", "--reload" ]
