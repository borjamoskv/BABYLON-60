// C5-REAL EXERGY CERTIFIED
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static int check_in_path(const char* tool_name) {
    char* path_env = getenv("PATH");
    if (path_env == NULL) {
        return 0; // PATH not set
    }

    // Duplicate path since strtok modifies the string
    char* path_copy = strdup(path_env);
    if (path_copy == NULL) {
        return 0;
    }

    char* dir = strtok(path_copy, ":");
    char full_path[1024];
    int found = 0;

    while (dir != NULL) {
        snprintf(full_path, sizeof(full_path), "%s/%s", dir, tool_name);
        if (access(full_path, X_OK) == 0) {
            found = 1;
            break;
        }
        dir = strtok(NULL, ":");
    }

    free(path_copy);
    return found;
}

static PyObject* verify_dependencies(PyObject* self, PyObject* args) {
    PyObject* py_list;

    if (!PyArg_ParseTuple(args, "O", &py_list)) {
        return NULL;
    }

    if (!PyList_Check(py_list)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a list of strings.");
        return NULL;
    }

    Py_ssize_t size = PyList_Size(py_list);
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(py_list, i);
        if (!PyUnicode_Check(item)) {
            PyErr_SetString(PyExc_TypeError, "List items must be strings.");
            return NULL;
        }

        const char* tool_name = PyUnicode_AsUTF8(item);
        if (!check_in_path(tool_name)) {
            fprintf(stderr, "\n[FATAL - KERNEL LEVEL] Missing Dependency: '%s'. HALTING LEDGER.\n", tool_name);
            fflush(stderr);
            abort(); // Native hardware abort
        }
    }

    Py_RETURN_NONE;
}

static PyMethodDef CortexGuardMethods[] = {
    {"verify_dependencies", verify_dependencies, METH_VARARGS, "Verify OS dependencies at the kernel level."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef cortexguardmodule = {
    PyModuleDef_HEAD_INIT,
    "cortex_guard_core",
    "ULTRATHINK Zero-Tolerance Dependency Vanguard (Native C).",
    -1,
    CortexGuardMethods
};

PyMODINIT_FUNC PyInit_cortex_guard_core(void) {
    return PyModule_Create(&cortexguardmodule);
}
