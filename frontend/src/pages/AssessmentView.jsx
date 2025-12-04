import React from "react";
import QuestionCard from "./QuestionCard";

const AssessmentView = ({ questions }) => {
  const handleDownload = (id) => {
    window.open(`http://127.0.0.1:8000/api/assessment/download/${id}/`, "_blank");
  };

  return (
    <div className="max-w-5xl mx-auto mt-10">
      <h2 className="text-2xl font-semibold text-[#5b4636] mb-6">
        Generated Assessment
      </h2>

      {questions.map((q, idx) => (
        <QuestionCard key={idx} q={q} idx={idx} handleDownload={handleDownload} />
      ))}
    </div>
  );
};

export default AssessmentView;
