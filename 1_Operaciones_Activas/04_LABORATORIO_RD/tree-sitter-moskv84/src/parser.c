#include <stdint.h>
#include <stdbool.h>

struct TSLanguage {
    uint32_t version;
    uint32_t symbol_count;
    uint32_t alias_count;
    uint32_t token_count;
    uint32_t external_token_count;
    uint32_t state_count;
    uint32_t large_state_count;
    uint32_t production_id_count;
    uint32_t field_count;
    uint16_t max_alias_sequence_length;
};

typedef struct TSLanguage TSLanguage;

const TSLanguage *tree_sitter_moskv84(void) {
    static const TSLanguage language = {
        .version = 14,
        .symbol_count = 1,
        .alias_count = 0,
        .token_count = 1,
        .external_token_count = 0,
        .state_count = 1,
        .large_state_count = 0,
        .production_id_count = 0,
        .field_count = 0,
        .max_alias_sequence_length = 0
    };
    return &language;
}
