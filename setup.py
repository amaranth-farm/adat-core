from setuptools import setup, find_packages


def scm_version():
    def local_scheme(version):
        return version.format_choice("+{node}", "+{node}.dirty")
    return {
        "relative_to": __file__,
        "version_scheme": "guess-next-dev",
        "local_scheme": local_scheme,
    }

setup(
    name="adat",
    use_scm_version=scm_version(),
    author="Hans Baier",
    author_email="hansfbaier@gmail.com",
    description="ADAT transmitter and receiver FPGA cores implemented in nmigen",
    license="CERN-OHL-W-2.0",
    setup_requires=["wheel", "setuptools", "setuptools_scm"],
    install_requires=[
        "nmigen>=0.2,<0.4",
        "importlib_metadata; python_version<'3.8'",
    ],
    dependency_links=["git+https://github.com/hansfbaier/nmigen-library.git"],
    packages=find_packages(),
    project_urls={
        "Source Code": "https://github.com/hansfbaier/adat-core",
        "Bug Tracker": "https://github.com/hansfbaier/adat-core/issues",
    },
)

