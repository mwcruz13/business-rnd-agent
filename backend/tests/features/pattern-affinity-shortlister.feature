Feature: Pattern affinity shortlister
  The deterministic affinity matrix must produce a ranked shortlist of
  Strategyzer business model patterns given a signal zone, classification,
  and disruption filters from Step 1.

  Scenario: Nonconsumption signal with new-market classification yields INVENT direction
    Given a signal with zone "Nonconsumption" and classification "Disruptive — New-Market"
    When the affinity shortlister runs
    Then the direction is "invent"
    And the shortlist contains "Market Explorers"
    And the shortlist contains "Cost Differentiators"
    And every shortlisted pattern belongs to the "invent" library

  Scenario: Overserved customers signal with low-end classification yields SHIFT direction
    Given a signal with zone "Overserved Customers" and classification "Disruptive — Low-End"
    When the affinity shortlister runs
    Then the direction is "shift"
    And the shortlist contains "High Cost to Low Cost"
    And the shortlist contains "Conventional to Contrarian"
    And every shortlisted pattern belongs to the "shift" library

  Scenario: Enabling technology signal with ambiguous classification yields both directions
    Given a signal with zone "Enabling Technology" and classification "Sustaining"
    When the affinity shortlister runs
    Then the direction is "shift"
    And the shortlist is not empty

  Scenario: Business model anomaly with new-market classification yields INVENT
    Given a signal with zone "Business Model Anomaly" and classification "Disruptive — New-Market"
    When the affinity shortlister runs
    Then the direction is "invent"
    And the shortlist contains "Revenue Differentiators"

  Scenario: Disruption filters boost relevant patterns in the shortlist
    Given a signal with zone "Nonconsumption" and classification "Disruptive — New-Market"
    And the signal has disruption filters "Barrier Removal" and "Asymmetric Motivation"
    When the affinity shortlister runs
    Then "Market Explorers" scores higher than "Activity Differentiators"

  Scenario: Low-end foothold with performance overshoot filter boosts cost patterns
    Given a signal with zone "Low-End Foothold" and classification "Disruptive — Low-End"
    And the signal has disruption filters "Performance Overshoot"
    When the affinity shortlister runs
    Then the direction is "shift"
    And the shortlist contains "High Cost to Low Cost"
    And the shortlist contains "Conventional to Contrarian"

  Scenario: Shortlist respects the maximum result count
    Given a signal with zone "Nonconsumption" and classification "Disruptive — New-Market"
    And the maximum shortlist size is 2
    When the affinity shortlister runs
    Then the shortlist has at most 2 entries

  Scenario: Unknown zone with non-disruptive classification defaults to both directions
    Given a signal with zone "Unknown Future Zone" and classification "Emerging"
    When the affinity shortlister runs
    Then the direction is "both"
