#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

typedef uint64_t ulong;
typedef uint32_t uint;
typedef uint8_t uchar;

#define FD_FUNK_TXN_ROOT 0

typedef struct {
    ulong xid;
    int is_root;
    char data[64];
} fd_funk_txn_t;

typedef struct {
    fd_funk_txn_t* root;
    fd_funk_txn_t* last_publish;
} fd_accdb_t;

// Simulated global database
fd_accdb_t global_db;

// Mock function representing fd_funk_rec_query_try
char* fd_funk_rec_query_try(fd_accdb_t* db, ulong xid) {
    // If the reader sees last_publish pointing to a different xid,
    // it falls back to the root state if it cannot find the transaction state fully migrated.
    // In the ghosting window, last_publish has advanced, but records haven't migrated.
    if (db->last_publish != NULL && db->last_publish->xid == xid) {
        // Assume reader gets redirected to ROOT during the race window because TXN is marked 'published'
        // but its records are not yet available in ROOT.
        return db->root->data;
    }
    return NULL;
}

int main() {
    printf("Starting Firedancer Funk State Ghosting PoC...\n");

    fd_funk_txn_t root_txn;
    root_txn.xid = FD_FUNK_TXN_ROOT;
    root_txn.is_root = 1;
    strcpy(root_txn.data, "ROOT_DATA_STALE");

    fd_funk_txn_t new_txn;
    new_txn.xid = 1001;
    new_txn.is_root = 0;
    strcpy(new_txn.data, "NEW_TXN_DATA");

    global_db.root = &root_txn;
    global_db.last_publish = &root_txn; // Initially points to root

    printf("\n[Step 1] Creating record in non-root transaction TXN_A (xid 1001)...\n");
    // new_txn created above.

    printf("[Step 2] Updating global last_publish to TXN_A (Ghosting Window OPEN)...\n");
    // Atomic swap in fd_accdb_txn_publish_one (simulated)
    global_db.last_publish = &new_txn;

    printf("[Step 3] Querying record concurrently via fd_funk_rec_query_try...\n");
    char* result = fd_funk_rec_query_try(&global_db, 1001);

    printf("\nPoC Result:\n");
    if (result != NULL && strcmp(result, "ROOT_DATA_STALE") == 0) {
        printf("  Read data: %s\n", result);
        printf("SUCCESS: Ghosting condition hit! Reader returned stale ROOT data instead of NEW_TXN_DATA.\n");
    } else {
        printf("FAIL: No ghosting detected.\n");
    }

    printf("\n[Step 4] Migrating records from TXN_A to ROOT (Ghosting Window CLOSED)...\n");
    strcpy(global_db.root->data, new_txn.data);

    char* post_result = fd_funk_rec_query_try(&global_db, 1001);
    printf("Post-migration Read data: %s\n", post_result);

    return 0;
}
