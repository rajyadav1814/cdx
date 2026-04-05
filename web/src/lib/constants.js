export const AGENTS = {
  1: {
    id: 1, key: 'agent1',
    name: 'Opportunity Discovery', sub: 'Where to Play',
    color: '#1D9E75', hasChat: false,
  },
  2: {
    id: 2, key: 'agent2',
    name: 'Strategy Synthesis', sub: 'How to Play',
    color: '#8B7FE8', hasChat: true,
  },
  3: {
    id: 3, key: 'agent3',
    name: 'Audience-Fit', sub: 'Who to Play With',
    color: '#4A9EE8', hasChat: true,
  },
  4: {
    id: 4, key: 'agent4',
    name: 'ROI Forecast', sub: 'Is It Worth It?',
    color: '#D4924A', hasChat: true,
  },
}

export const AGENT_SUGGESTIONS = {
  agent2: [
    "Which artist is the best fit for a beverage brand?",
    "What activation strategy do you recommend for the top artist?",
    "Which artist has the strongest cultural narrative?",
    "What are the sentiment risks I should know about?",
  ],
  agent3: [
    "Which artist has the largest audience in Mexico?",
    "How confident are we in the audience data?",
    "Which artist best matches an 18-34 female demographic?",
    "Which markets have the strongest first-party data?",
  ],
  agent4: [
    "Which artist gives the best ROI at $150K investment?",
    "Walk me through the optimistic scenario for the top artist?",
    "Which artists have risk flags I should be aware of?",
    "How do projections compare to past campaign actuals?",
  ],
}
