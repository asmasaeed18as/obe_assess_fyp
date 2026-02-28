import React from "react";
import { FileText, CheckCircle } from "lucide-react";

const QuestionCard = ({ q, idx }) => {
  const bloom = q.meta?.bloom || q.bloomLevel || "N/A";
  const clo = q.meta?.clo || "";

  return (
    <div className="glass-result-card">
      <div className="card-top-row">
        <div className="q-number-pill">Question {idx + 1}</div>
        <div className="tags-group">
          <span className="badge-outline">{bloom}</span>
          <span className="badge-primary">{q.marks || q.weightage} Marks</span>
        </div>
      </div>

      <p className="question-text">{q.question}</p>

      {q.answer && (
        <div className="answer-section">
          <div className="answer-label">
            <CheckCircle size={14} /> Model Answer
          </div>
          <p>{q.answer}</p>
        </div>
      )}
    </div>
  );
};

export default QuestionCard;