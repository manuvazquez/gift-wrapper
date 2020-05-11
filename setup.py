import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gift-wrapper", # Replace with your own username
    version="1.3",
    author="Manuel A. Vázquez",
    author_email="manuavazquez@gmail.com",
    description="Build GIFT (Moodle compatible) files easily",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/manuvazquez/gift-wrapper",
    packages=setuptools.find_packages(),
    install_requires=['paramiko>=2.7.1', 'colorama>=0.4.3', 'PyYAML>=5.3.1', 'tqdm>=4.44.1'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Environment :: Console",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['wrap.py=gift_wrapper.core:main'],
    }
)
