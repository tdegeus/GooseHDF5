
# required to specify the c++ standard
cmake_minimum_required(VERSION 3.0)

# required for install
include(CMakePackageConfigHelpers)
include(GNUInstallDirs)

# project settings
# ----------------

# name
project(GooseHDF5)

# binaries
set(binaries
  "bin/G5list"
  "bin/G5repair"
  "bin/G5merge"
  "bin/G5select"
  "bin/G5find"
  "bin/G5check"
)

# version info
set(GOOSEHDF5_VERSION_NUMBER "0.0.1")

# options
# -------

# install binaries
option(BIN "Install binaries" ON)

# install binaries
if(BIN)
  install(PROGRAMS ${CMAKE_CURRENT_SOURCE_DIR}/${binaries} DESTINATION bin)
endif()

# print information to screen
# ---------------------------

message(STATUS "")
message(STATUS "+---------------------------------------------------------------------------------")
message(STATUS "|")
message(STATUS "| Use 'make install' to install in")
message(STATUS "|   ${CMAKE_INSTALL_PREFIX}")
message(STATUS "|")
message(STATUS "| To specify a custom directory call")
message(STATUS "|   cmake /path/to/${PROJECT_NAME} -DCMAKE_INSTALL_PREFIX=yourprefix")
message(STATUS "|")
message(STATUS "| For custom paths, add the following line to your '~/.bashrc'")
message(STATUS "|   export PKG_CONFIG_PATH=${CMAKE_INSTALL_PREFIX}/share/pkgconfig:$PKG_CONFIG_PATH")
message(STATUS "|")
message(STATUS "+---------------------------------------------------------------------------------")
message(STATUS "")
