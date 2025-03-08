"""Tests for the ExecutableCollection model."""

from wish_models.executable_collection import ExecutableCollection
from wish_models.test_factories.executable_collection_factory import ExecutableCollectionFactory


class TestExecutableCollection:
    """Test cases for the ExecutableCollection model."""

    def test_executable_collection_creation(self):
        """Test that an ExecutableCollection instance can be created."""
        collection = ExecutableCollection()
        assert collection.executables == []

    def test_add_executable(self):
        """Test that executables can be added to the collection."""
        collection = ExecutableCollection()

        # Add executable with minimum required fields
        collection.add_executable(path="/usr/bin/python")
        assert len(collection.executables) == 1
        assert collection.executables[0].path == "/usr/bin/python"
        assert collection.executables[0].size is None
        assert collection.executables[0].permissions is None

        # Add executable with all fields
        collection.add_executable(
            path="/usr/bin/bash",
            size=12345,
            permissions="rwxr-xr-x"
        )
        assert len(collection.executables) == 2
        assert collection.executables[1].path == "/usr/bin/bash"
        assert collection.executables[1].size == 12345
        assert collection.executables[1].permissions == "rwxr-xr-x"

    def test_group_by_directory(self):
        """Test that executables can be grouped by directory."""
        collection = ExecutableCollection()

        # Add executables in different directories
        collection.add_executable(path="/usr/bin/python")
        collection.add_executable(path="/usr/bin/bash")
        collection.add_executable(path="/usr/local/bin/node")
        collection.add_executable(path="/usr/local/bin/npm")

        grouped = collection.group_by_directory()

        assert len(grouped) == 2
        assert len(grouped["/usr/bin"]) == 2
        assert len(grouped["/usr/local/bin"]) == 2

        # Check that the executables are in the correct groups
        assert grouped["/usr/bin"][0].filename == "python"
        assert grouped["/usr/bin"][1].filename == "bash"
        assert grouped["/usr/local/bin"][0].filename == "node"
        assert grouped["/usr/local/bin"][1].filename == "npm"

    def test_executable_collection_factory(self):
        """Test that ExecutableCollectionFactory creates valid instances."""
        # Test default factory
        collection = ExecutableCollectionFactory()

        assert len(collection.executables) == 3
        assert collection.executables[0].path == "/usr/bin/test1"
        assert collection.executables[1].path == "/usr/bin/test2"
        assert collection.executables[2].path == "/usr/local/bin/test3"

    def test_create_with_executables(self):
        """Test that create_with_executables creates a valid instance."""
        paths = ["/usr/bin/python", "/usr/bin/bash", "/usr/local/bin/node"]
        collection = ExecutableCollectionFactory.create_with_executables(paths)

        assert len(collection.executables) == 3
        assert collection.executables[0].path == "/usr/bin/python"
        assert collection.executables[1].path == "/usr/bin/bash"
        assert collection.executables[2].path == "/usr/local/bin/node"

    def test_create_with_directory_structure(self):
        """Test that create_with_directory_structure creates a valid instance."""
        directory_structure = {
            "/usr/bin": ["python", "bash"],
            "/usr/local/bin": ["node", "npm"]
        }
        collection = ExecutableCollectionFactory.create_with_directory_structure(directory_structure)

        assert len(collection.executables) == 4

        # Group by directory to verify structure
        grouped = collection.group_by_directory()

        assert len(grouped) == 2
        assert len(grouped["/usr/bin"]) == 2
        assert len(grouped["/usr/local/bin"]) == 2

        # Check filenames in each directory
        filenames_usr_bin = [exe.filename for exe in grouped["/usr/bin"]]
        filenames_usr_local_bin = [exe.filename for exe in grouped["/usr/local/bin"]]

        assert "python" in filenames_usr_bin
        assert "bash" in filenames_usr_bin
        assert "node" in filenames_usr_local_bin
        assert "npm" in filenames_usr_local_bin
