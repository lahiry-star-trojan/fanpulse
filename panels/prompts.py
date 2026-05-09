def build_prompt(trends_summary, ticket_summary, sentiment_summary):
    system = (
        'You are a senior sports analytics briefing agent for FIFA World Cup 2026 '
        'host city organizers and commercial partners. Produce concise, data-driven '
        'executive briefings. Use specific numbers, city names, and team names. '
        'Structure: 3 sections (Demand Highlights, Ticket Intelligence, Sentiment Signals). '
        'End with 3 bullet recommendations. Max 200 words total.'
    )
    user = (
        f'Generate this week\'s fan engagement briefing:\n\n'
        f'DEMAND DATA:\n{trends_summary}\n\n'
        f'TICKET DATA:\n{ticket_summary}\n\n'
        f'SENTIMENT DATA:\n{sentiment_summary}\n\n'
        'Write the 200-word executive briefing now.'
    )
    return system, user