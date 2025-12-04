import React from "react";

const QuestionCard = ({ q, idx, handleDownload }) => (
  <div className="bg-[#fefaf3] border border-[#e0c9a6] rounded-2xl p-6 mb-6 shadow-md hover:shadow-lg transition-all duration-300">
    {/* Header */}
    <div className="flex justify-between items-center">
      <h3 className="text-lg font-semibold text-[#5b4636]">
        Question {idx + 1}
      </h3>
      <div className="flex gap-2 items-center">
        <span className="text-sm px-3 py-1 bg-[#d4a373] text-white rounded-full">
          {q.bloomLevel || ""}
        </span>

        {/* <button
          onClick={() => handleDownload(q.id)}
          className="text-sm px-3 py-1 bg-[#d4a373] text-white rounded-md hover:bg-[#b5835a] transition"
        >
          Download PDF
        </button> */}
      </div>
    </div>

    <p className="mt-3 text-gray-800 text-[1rem] leading-relaxed">{q.question}</p>

    {q.answer && (
      <div className="mt-4 bg-[#fffaf4] border border-[#ecd9c6] p-3 rounded-lg">
        <p className="text-sm text-[#4a3f35]">
          <strong className="text-[#d4a373]">Model Answer:</strong> {q.answer}
        </p>
      </div>
    )}

    {q.rubric && (
      <div className="mt-5">
        <h4 className="text-md font-semibold text-[#5b4636] mb-2">Rubric:</h4>
        <ul className="list-disc ml-6 space-y-1 text-sm text-[#4a3f35]">
          <li><strong>Excellent:</strong> {q.rubric.Excellent}</li>
          <li><strong>Average:</strong> {q.rubric.Average}</li>
          <li><strong>Poor:</strong> {q.rubric.Poor}</li>
        </ul>
      </div>
    )}
  </div>
);

export default QuestionCard;
