import React, { useContext } from "react";
import AuthContext from "../contexts/AuthContext";
import InstructorCourseDetail from "./InstructorCourseDetail";
import StudentCourseDetail from "./StudentCourseDetail";

const CourseDetail = () => {
  const { user } = useContext(AuthContext);

  // Normalize the role string just like we did in DashboardHome
  const role = user?.role?.toLowerCase() || "student";

  // If they are an instructor, give them the page with all the buttons
  if (role === "instructor") {
    return <InstructorCourseDetail />;
  }

  // Otherwise, give them the clean, read-only student page
  return <StudentCourseDetail />;
};

export default CourseDetail;