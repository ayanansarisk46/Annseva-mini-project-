"""
================================================================================
AnnSeva - NGO Matching Engine (services/matching.py)
================================================================================
College Viva Explanation:
-------------------------
Question: "How does the matching logic work in AnnSeva?"
Answer:
1. When a donor registers a food donation, this module retrieves all active NGOs.
2. It parses the donor's physical pickup address and extracts locality and city keywords.
3. It compares these keywords against the service locations of all registered NGOs:
   - Primary Priority: Exact locality/area match (e.g. Andheri to Andheri, Bandra to Bandra).
   - Secondary Priority: Broader city match (e.g. Mumbai, Pune, Delhi).
4. The NGO with the highest matching locality score is selected.
5. If no exact match is found, the system assigns the first available active community NGO.
6. The selected NGO ID is assigned to the donation, and an automated alert notification
   is dispatched to the NGO.
================================================================================
"""

import re
from models import User

# Common stopwords to ignore during matching
STOPWORDS = {'near', 'opp', 'opposite', 'behind', 'beside', 'road', 'rd', 'street', 
             'st', 'lane', 'nagar', 'colony', 'area', 'sector', 'block', 'plot', 
             'floor', 'building', 'bldg', 'complex', 'cross', 'main', 'the', 'and', 'at', 'in'}

def extract_tokens(address_str):
    """Tokenizes and cleans an address string into significant location keywords."""
    if not address_str:
        return set()
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', address_str.lower())
    words = cleaned.split()
    return {w for w in words if w not in STOPWORDS and len(w) > 2}

def match_suitable_ngo(donation_location):
    """
    Finds the most suitable and nearest NGO for a food donation using locality & city matching.

    Parameters:
        donation_location (str): Physical address / area of food pickup.

    Returns:
        tuple: (selected_ngo_user_object, match_reason_str)
               Returns (None, reason) if no registered NGOs exist.
    """
    # 1. Fetch all registered NGOs from database
    ngos = User.query.filter_by(role='NGO').all()
    if not ngos:
        return None, "No registered NGOs available in the system."

    donor_tokens = extract_tokens(donation_location)

    best_ngo = None
    best_score = -1
    best_matched_terms = []

    # Known high-priority locality keywords (urban centers)
    primary_localities = {'andheri', 'bandra', 'kurla', 'dadar', 'powai', 'thane', 
                          'borivali', 'malad', 'ghatkopar', 'chembur', 'vashi', 
                          'colaba', 'pune', 'delhi', 'bangalore', 'mumbai'}

    for ngo in ngos:
        ngo_tokens = extract_tokens(ngo.location)
        overlap = donor_tokens.intersection(ngo_tokens)
        
        # Calculate weighted score: primary locality matches get higher priority (3 points each)
        score = 0
        matched = []
        for term in overlap:
            if term in primary_localities:
                score += 3
            else:
                score += 1
            matched.append(term.capitalize())

        if score > best_score:
            best_score = score
            best_ngo = ngo
            best_matched_terms = matched

    # If an area overlap was found
    if best_ngo and best_score > 0:
        terms_str = ", ".join(best_matched_terms)
        return best_ngo, f"Matched by local area & city proximity: [{terms_str}] with {best_ngo.name}."

    # Fallback: Assign first available active community NGO
    default_ngo = ngos[0]
    return default_ngo, f"Assigned to primary available community NGO ({default_ngo.name})."
