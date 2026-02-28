import React from "react";

const QuestionCard = ({ q, idx }) => {
  // Safe access to meta data
  const bloom = q.meta?.bloom || q.bloomLevel || "N/A";
  const clo = q.meta?.clo || "";

  return (
    <div className="bg-[#fefaf3] border border-[#e0c9a6] rounded-2xl p-6 mb-6 shadow-md hover:shadow-lg transition-all duration-300">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-[#5b4636]">
          Question {idx + 1}
        </h3>
        <div className="flex gap-2 items-center">
          {/* Marks Badge */}
          <span className="text-xs px-2 py-1 bg-[#8d6e63] text-white rounded-md font-semibold">
            {q.marks || q.weightage} Marks
          </span>
          {/* Bloom Badge */}
          <span className="text-xs px-3 py-1 bg-[#d4a373] text-white rounded-full font-semibold shadow-sm">
            {bloom} {clo ? `| ${clo}` : ""}
          </span>
        </div>
      </div>

      {/* Question Text */}
      <p className="text-gray-800 text-[1.05rem] leading-relaxed font-medium mb-4">
        {q.question}
      </p>

      {/* ✅ THE FIX: Dynamically render Options if they exist */}
      {q.options && Array.isArray(q.options) && q.options.length > 0 && (
        <div className="mb-5 pl-2 md:pl-4 space-y-2">
          {q.options.map((opt, i) => (
            <div 
              key={i} 
              className="flex items-start bg-white p-3 rounded-lg border border-[#ecd9c6] shadow-sm"
            >
              <span className="text-gray-700 font-medium">{opt}</span>
            </div>
          ))}
        </div>
      )}

      {/* Model Answer */}
      {q.answer && (
        <div className="mt-5 bg-[#fffaf4] border-l-4 border-[#d4a373] p-4 rounded-r-lg shadow-sm">
          <p className="text-sm text-[#4a3f35]">
            <strong className="text-[#8d6e63] block mb-1 uppercase tracking-wide text-xs">Model Answer:</strong> 
            {q.answer}
          </p>
        </div>
      )}

      {/* Grading Rubric */}
      {q.rubric && (
        <div className="mt-5 pt-4 border-t border-[#ecd9c6]">
          <h4 className="text-sm font-bold text-[#5b4636] mb-2 uppercase tracking-wide">Grading Rubric:</h4>
          <ul className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <li className="bg-white p-2 rounded border border-gray-100 text-sm shadow-sm">
              <strong className="text-green-600 block text-xs mb-1">Excellent</strong> 
              <span className="text-gray-600 text-xs">{q.rubric.Excellent}</span>
            </li>
            <li className="bg-white p-2 rounded border border-gray-100 text-sm shadow-sm">
              <strong className="text-yellow-600 block text-xs mb-1">Average</strong> 
              <span className="text-gray-600 text-xs">{q.rubric.Average}</span>
            </li>
            <li className="bg-white p-2 rounded border border-gray-100 text-sm shadow-sm">
              <strong className="text-red-500 block text-xs mb-1">Poor</strong> 
              <span className="text-gray-600 text-xs">{q.rubric.Poor}</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default QuestionCard;