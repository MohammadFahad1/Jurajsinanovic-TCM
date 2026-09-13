from rest_framework import serializers
from health_check.models import Question, Answer, UserCheckIn, UserAnswer


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


class UserCheckinAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['id', 'check_in', 'question', 'answer', 'score', 'created_at', 'updated_at']
        read_only_fields = ['check_in', 'score', 'created_at', 'updated_at']

class UserCheckInSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField(read_only=True)
    total_answered = serializers.SerializerMethodField(read_only=True)
    pattern = serializers.SerializerMethodField(read_only=True)
    answers = UserCheckinAnswerSerializer(many=True, required=False)

    class Meta:
        model = UserCheckIn
        fields = ['id', 'user', 'status', 'score', 'total_answered', 'pattern', 'answers', 'created_at', 'updated_at']
        read_only_fields = ['user', 'status', 'score', 'total_answered', 'pattern']

    def get_score(self, obj):
        return obj.calculate_score()

    def get_total_answered(self, obj):
        return obj.answers.count()

    def get_pattern(self, obj):
        score = obj.calculate_score()
        if score < 40:
            return 'Cold'
        elif score <= 80:
            return 'Balanced'
        elif score <= 100:
            return 'Heat'
        return 'Cold-Heat Imbalance'

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        if answers_data:
            validated_data['status'] = UserCheckIn.COMPLETED
        user_check_in = UserCheckIn.objects.create(**validated_data)
        for answer_data in answers_data:
            answer_obj = answer_data.get('answer')
            score = answer_data.get('score')
            if score is None and answer_obj:
                score = answer_obj.score
            UserAnswer.objects.create(check_in=user_check_in, score=score or 0, **answer_data)
        return user_check_in

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        instance.status = validated_data.get('status', instance.status)
        instance.save()

        if answers_data is not None:
            instance.answers.all().delete()
            for answer_data in answers_data:
                answer_obj = answer_data.get('answer')
                score = answer_data.get('score')
                if score is None and answer_obj:
                    score = answer_obj.score
                UserAnswer.objects.create(check_in=instance, score=score or 0, **answer_data)

        return instance

