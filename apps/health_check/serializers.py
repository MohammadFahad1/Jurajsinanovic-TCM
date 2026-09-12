from rest_framework import serializers
from health_check.models import Question, Answer

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'answer', 'score', 'created_at', 'updated_at']
        read_only_fields = ['question']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, required=False)
    option_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'title', 'answers', 'option_count', 'created_at', 'updated_at']

    def get_option_count(self, obj):
        return obj.answers.count()

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        return question

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        instance.title = validated_data.get('title', instance.title)
        instance.save()

        if answers_data is not None:
            instance.answers.all().delete()
            for answer_data in answers_data:
                Answer.objects.create(question=instance, **answer_data)

        return instance


