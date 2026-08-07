from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import ai_service


class EducationCopilot:
    def __init__(self, db: AsyncSession): self.db = db

    async def plan_lesson(self, subject, grade, topic, duration):
        p = f"""Create a lesson plan.
Subject: {subject}, Grade: {grade}, Topic: {topic}, Duration: {duration} minutes
Include: learning objectives, materials needed, introduction, main activities, assessment, homework."""
        return await ai_service.complete(p)

    async def create_assessment(self, subject, grade, topic, question_count, question_types):
        p = f"""Create an assessment.
Subject: {subject}, Grade: {grade}, Topic: {topic}
Questions: {question_count}, Types: {question_types}
Include: questions, answer key, difficulty distribution, time estimate."""
        return await ai_service.complete(p)

    async def generate_study_plan(self, subject, topics, duration):
        p = f"""Create a study plan.
Subject: {subject}, Topics: {topics}, Duration: {duration}
Provide: weekly schedule, key concepts, practice activities, resources, progress checkpoints."""
        return await ai_service.complete(p)

    async def analyze_student_performance(self, performance_data):
        p = f"""Analyze student performance data: {performance_data}
Provide: strengths, weaknesses, improvement suggestions, personalized recommendations."""
        return await ai_service.complete(p)
