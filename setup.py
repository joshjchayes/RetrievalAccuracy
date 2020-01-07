'''
setup script for RetrievalAccuracy

'''

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="retrievalaccuracy",
    version="0.1.0",
    author="Joshua Hayes",
    author_email="joshjchayes@gmail.com",
    description="Metrics for evaluating the accuracy of parameter retrieval results",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joshjchayes/RetrievalAccuracy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta"
    ],
    python_requires='>=3.6',
    install_requires=['scipy', 'numpy']
)
