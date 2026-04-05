export default function SuggestedQuestions({ questions, onSelect }) {
  return (
    <div className="p-4 grid grid-cols-2 gap-2">
      {questions.map((q, i) => (
        <button
          key={i}
          className="bg-bg-surface2 border border-white/[0.06] rounded-sm p-3 text-sm text-text-secondary hover:text-text-primary hover:border-white/[0.12] cursor-pointer text-left transition-colors duration-100"
          style={{ appearance: 'none', fontFamily: 'inherit' }}
          onClick={() => onSelect(q)}
        >
          {q}
        </button>
      ))}
    </div>
  )
}
