import React from "react";
import { render, screen } from "@testing-library/react";

import QuestionCard from "../QuestionCard";

describe("QuestionCard", () => {
  it("renders question text, options, answer, and rubric", () => {
    render(
      <QuestionCard
        idx={0}
        q={{
          question: "What is unit testing?",
          marks: 5,
          options: ["A. One", "B. Two"],
          answer: "Testing individual units.",
          rubric: {
            Excellent: "Clear explanation",
            Average: "Partial explanation",
            Poor: "Incorrect answer",
          },
          meta: { bloom: "C2", clo: "CLO-1" },
        }}
      />
    );

    expect(screen.getByText("Question 1")).toBeInTheDocument();
    expect(screen.getByText("What is unit testing?")).toBeInTheDocument();
    expect(screen.getByText("A. One")).toBeInTheDocument();
    expect(screen.getByText("Testing individual units.")).toBeInTheDocument();
    expect(screen.getByText("Grading Rubric:")).toBeInTheDocument();
    expect(screen.getByText("C2")).toBeInTheDocument();
  });

  it("falls back when optional data is missing", () => {
    render(<QuestionCard idx={1} q={{ question: "Explain integration testing", weightage: 10 }} />);

    expect(screen.getByText("Question 2")).toBeInTheDocument();
    expect(screen.getByText("N/A")).toBeInTheDocument();
    expect(screen.getByText("10 Marks")).toBeInTheDocument();
  });
});
