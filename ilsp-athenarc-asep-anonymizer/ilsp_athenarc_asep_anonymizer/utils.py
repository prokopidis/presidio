def enrich_entity_info(original_text: str, masked_text: str, entities: list) -> list:
    """
    Enriches entity dictionaries with information from the original text.
    
    Args:
        original_text: The original unmasked text
        masked_text: The text with masked entities
        entities: List of entity dictionaries with 'start' and 'end' positions in masked text
        
    Returns:
        List of enriched entity dictionaries with added fields:
        - start_position: Starting position in original text
        - end_position: Ending position in original text
        - orig_text: Original text of the entity
    """
    # Create mappings between masked text and original text
    original_idx = 0
    masked_idx = 0
    mask_to_orig_start = {}  # Maps start positions in masked text to original text
    mask_to_orig_end = {}    # Maps end positions in masked text to original text
    
    while masked_idx < len(masked_text) and original_idx < len(original_text):
        # Check if we're at the beginning of a mask in the masked text
        if masked_text[masked_idx:].startswith("{{"):
            # Save the start position mapping
            mask_to_orig_start[masked_idx] = original_idx
            
            # Find the end of this mask
            end_mask_idx = masked_text.find("}}", masked_idx) + 2
            if end_mask_idx == 1:  # Not found
                break
            
            # Find the entity text in the original text
            # We need to look ahead to find where the text continues after the mask
            next_char_idx = end_mask_idx
            while next_char_idx < len(masked_text) and masked_text[next_char_idx].isspace():
                next_char_idx += 1
                
            # If we're at the end of the text, the entity extends to the end
            if next_char_idx >= len(masked_text):
                entity_end_idx = len(original_text)
            else:
                # Find the next matching point in original text
                next_char = masked_text[next_char_idx]
                
                # Find this character in the original text starting from current position
                search_start = original_idx
                while search_start < len(original_text):
                    match_idx = original_text.find(next_char, search_start)
                    if match_idx == -1:
                        entity_end_idx = len(original_text)
                        break
                    
                    # Check if this is a genuine continuation point
                    # by making sure the following text matches
                    can_continue = True
                    check_idx = 1
                    while next_char_idx + check_idx < len(masked_text) and match_idx + check_idx < len(original_text):
                        if masked_text[next_char_idx + check_idx] != original_text[match_idx + check_idx]:
                            can_continue = False
                            break
                        check_idx += 1
                    
                    if can_continue:
                        entity_end_idx = match_idx
                        break
                    
                    search_start = match_idx + 1
                
                if search_start >= len(original_text):
                    entity_end_idx = len(original_text)
            
            # Save the end position mapping
            mask_to_orig_end[end_mask_idx] = entity_end_idx
            
            # Update indices
            masked_idx = end_mask_idx
            original_idx = entity_end_idx
        else:
            # Regular character
            if masked_text[masked_idx] == original_text[original_idx]:
                # Store position mapping
                mask_to_orig_start[masked_idx] = original_idx
                mask_to_orig_end[masked_idx + 1] = original_idx + 1
                
                # Move forward both indices
                masked_idx += 1
                original_idx += 1
            else:
                # Characters don't match, move forward in original text
                original_idx += 1
    
    # Process each entity using the mapping
    enriched_entities = []
    for entity in entities:
        entity_start = entity['start']
        entity_end = entity['end']
        
        if entity_start in mask_to_orig_start and entity_end in mask_to_orig_end:
            start_position = mask_to_orig_start[entity_start]
            end_position = mask_to_orig_end[entity_end]
            orig_text = original_text[start_position:end_position]
            
            enriched_entity = entity.copy()
            enriched_entity.update({
                'start_position': start_position,
                'end_position': end_position,
                'orig_text': orig_text
            })
            enriched_entities.append(enriched_entity)
        else:
            # If we can't find the mapping, try to compute it
            print(f"Warning: Couldn't find direct mapping for entity at {entity_start}:{entity_end}")
            enriched_entities.append(entity)
    
    return enriched_entities


def match_entities(original_text, masked_text, entities):
    """
    A more robust approach using string alignment and direct search.
    This is a fallback method that doesn't rely on complex position mapping.
    """
    results = []
    
    # Process each entity
    for entity in entities:
        # Extract context before and after the entity in masked text
        mask_start = entity['start']
        mask_end = entity['end']
        mask_entity = masked_text[mask_start:mask_end]
        
        # Get some context before and after (up to 20 chars)
        context_before_len = min(20, mask_start)
        context_before = masked_text[mask_start - context_before_len:mask_start]
        
        context_after_len = min(20, len(masked_text) - mask_end)
        context_after = masked_text[mask_end:mask_end + context_after_len]
        
        # Clean up context - remove any mask patterns
        context_before = ''.join([c for i, c in enumerate(context_before) 
                                 if not (c == '{' and i+1 < len(context_before) and context_before[i+1] == '{')])
        context_before = ''.join([c for i, c in enumerate(context_before) 
                                 if not (c == '}' and i+1 < len(context_before) and context_before[i+1] == '}')])
        
        context_after = ''.join([c for i, c in enumerate(context_after) 
                               if not (c == '{' and i+1 < len(context_after) and context_after[i+1] == '{')])
        context_after = ''.join([c for i, c in enumerate(context_after) 
                               if not (c == '}' and i+1 < len(context_after) and context_after[i+1] == '}')])
        
        # Find context in original text
        if context_before and context_after:
            # Try to find both contexts
            try:
                before_pos = original_text.index(context_before)
                before_end = before_pos + len(context_before)
                
                after_pos = original_text.find(context_after, before_end)
                
                if after_pos > before_end:
                    # Found both contexts
                    orig_start = before_end
                    orig_end = after_pos
                    orig_text = original_text[orig_start:orig_end]
                    
                    # Create enriched entity
                    enriched_entity = entity.copy()
                    enriched_entity.update({
                        'start_position': orig_start,
                        'end_position': orig_end,
                        'orig_text': orig_text
                    })
                    results.append(enriched_entity)
                    continue
            except ValueError:
                pass
        
        # Fallback: direct search based on surrounding context
        words_before = context_before.strip().split()
        words_after = context_after.strip().split()
        
        if words_before and words_after:
            try:
                last_word_before = words_before[-1]
                first_word_after = words_after[0]
                
                # Find these words in original text
                before_pos = original_text.find(last_word_before)
                if before_pos >= 0:
                    before_end = before_pos + len(last_word_before)
                    
                    # Find first word after
                    after_pos = original_text.find(first_word_after, before_end)
                    
                    if after_pos > before_end:
                        orig_start = before_end
                        orig_end = after_pos
                        orig_text = original_text[orig_start:orig_end].strip()
                        
                        # Create enriched entity
                        enriched_entity = entity.copy()
                        enriched_entity.update({
                            'start_position': orig_start,
                            'end_position': orig_end,
                            'orig_text': orig_text
                        })
                        results.append(enriched_entity)
                        continue
            except (ValueError, IndexError):
                pass
        
        # If all else fails, add the original entity
        results.append(entity)
    
    return results



# # Example usage
# def main():
#     original_text = ("Κατηγόρησαν τον δικηγόρο Τιερί Χερτσόγκ ότι επιχείρησε να δωροδοκήσει τον "
#                     "Ζιλμπέρ Αζιμπέρ, δικαστή στο Ακυρωτικό Δικαστήριο της Γαλλίας, με αντάλλαγμα "
#                     "απόρρητες πληροφορίες από άλλη έρευνα εναντίον του Σαρκοζί.")
    
#     masked_text = ("Κατηγόρησαν τον δικηγόρο {{PERSON}} ότι επιχείρησε να δωροδοκήσει τον {{PERSON}}, "
#                   "δικαστή στο Ακυρωτικό Δικαστήριο της {{LOCATION}}, με αντάλλαγμα απόρρητες "
#                   "πληροφορίες από άλλη έρευνα εναντίον του {{PERSON}}.")
    
#     entities = [
#         {'entity_value': '{{PERSON}}', 'start': 25, 'end': 35},
#         {'entity_value': '{{PERSON}}', 'start': 70, 'end': 80},
#         {'entity_value': '{{LOCATION}}', 'start': 119, 'end': 131},
#         {'entity_value': '{{PERSON}}', 'start': 198, 'end': 208}
#     ]
    
#     # Try both methods
#     enriched_entities = match_entities(original_text, masked_text, entities)
    
#     print("Enriched entities:")
#     for entity in enriched_entities:
#         print(entity)



# if __name__ == "__main__":
#     main()
#     test_entity_mapping()


import re

# Assume your compiled regex patterns are defined as provided:
PHONE1_REGEX = re.compile(r"(\+\d{1,2}[\s-])?(?!0+\s+,?$)\d{10}\s*,?")
PHONE2_REGEX = re.compile(r"(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
# PHONE3_REGEX has a leading '\s' and a capturing group around the number itself
PHONE3_REGEX = re.compile(r"\s(\+\d{1,2}\s\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})")

# Define a list of patterns and whether to use span(0) [whole match] or span(1) [group 1]
# based on the pattern definition and desired output span.
# PHONE3_REGEX explicitly captures the number *without* the leading space in group 1.
patterns_config = [
    (PHONE1_REGEX, False), # False indicates use match.span() (span(0))
    (PHONE2_REGEX, False),
    (PHONE3_REGEX, True)  # True indicates use match.span(1) (the first group)
]

def find_longest_pattern_matches(text: str, patterns_config: list) -> list[tuple[int, int]]:
    """
    Finds all matches of multiple regex patterns in a string, filters to keep
    only the longest unique spans, and returns their offsets.

    Args:
        text: The string to scan.
        patterns_config: A list of tuples, where each tuple contains:
                         (compiled_regex_object, use_group1_span: bool).
                         use_group1_span=True means use match.span(1), False means use match.span(0).

    Returns:
        A list of (start, end) tuples for the longest, unique, non-contained matches,
        sorted by start position.
    """
    all_raw_matches = []

    # 1. Collect all match spans from all patterns
    for pattern, use_group1_span in patterns_config:
        for match in pattern.finditer(text):
            if use_group1_span:
                # Use span of group 1, which excludes the leading whitespace in PHONE3_REGEX
                span = match.span(1)
            else:
                # Use span of the whole match for other patterns
                span = match.span()

            # Only add valid spans (group 1 might not match in complex patterns,
            # though it should for the given PHONE3_REGEX)
            if span != (-1, -1):
                all_raw_matches.append(span)

    # Remove duplicate spans (e.g., if multiple patterns match the exact same span)
    # Sorting here helps with the next filtering step, though not strictly required for correctness.
    all_raw_matches = sorted(list(set(all_raw_matches)))

    # 2. Filter to keep only the longest, non-contained matches
    final_longest_matches = []

    for span_i in all_raw_matches:
        is_contained_by_longer = False
        for span_j in all_raw_matches:
            # Don't compare a span with itself
            if span_i != span_j:
                # Check if span_j starts at or before span_i AND ends at or after span_i
                contains = span_j[0] <= span_i[0] and span_j[1] >= span_i[1]
                # Check if span_j is strictly longer than span_i
                strictly_longer = (span_j[1] - span_j[0]) > (span_i[1] - span_i[0])

                if contains and strictly_longer:
                    # Found a strictly longer span (span_j) that fully contains span_i.
                    # Discard span_i.
                    is_contained_by_longer = True
                    break # No need to check other spans against span_i

        # If span_i was not contained by any strictly longer span, keep it.
        if not is_contained_by_longer:
            final_longest_matches.append(span_i)

    # 3. Sort the final list by start position for consistent output
    final_longest_matches.sort()

    return final_longest_matches
