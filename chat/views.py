from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_POST

from .models import Message


@login_required
def chat_home(request):
    users = User.objects.exclude(id=request.user.id).annotate(
        unread_count=Count(
            'sent_messages',
            filter=Q(
                sent_messages__receiver=request.user,
                sent_messages__is_read=False
            )
        )
    )

    selected_user_id = request.GET.get('user')

    selected_user = None
    messages = []

    if selected_user_id:
        selected_user = get_object_or_404(User, id=selected_user_id)

        # Mark messages from this user as read
        Message.objects.filter(
            sender=selected_user,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)

        messages = Message.objects.filter(
            Q(sender=request.user, receiver=selected_user) |
            Q(sender=selected_user, receiver=request.user)
        )

    return render(request, 'chat/chat_room.html', {
        'users': users,
        'selected_user': selected_user,
        'messages': messages,
    })

@login_required
def send_message_api(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')
        replied_to_id = request.POST.get('replied_to_id')

        receiver = get_object_or_404(User, id=receiver_id)

        replied_to = None

        if replied_to_id:
            replied_to = get_object_or_404(
                Message,
                id=replied_to_id
            )

        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content,
            replied_to=replied_to
        )

        return JsonResponse({
            'success': True,
            'message': message.content,
            'sender': message.sender.username,
            'created_at': message.created_at.strftime('%H:%M')
        })

    return JsonResponse({'success': False})


@login_required
def get_new_messages_api(request):
    receiver_id = request.GET.get('receiver_id')
    receiver = get_object_or_404(User, id=receiver_id)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=receiver, deleted_for_sender=False)
        |
        Q(sender=receiver, receiver=request.user, deleted_for_receiver=False)
    )

    data = []

    for message in messages:

        replied_to_data = None

        if message.replied_to:
            replied_to_data = {
                'id': message.replied_to.id,
                'sender': message.replied_to.sender.username,
                'content': message.replied_to.content
            }

        data.append({
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.strftime('%H:%M'),
            'is_read': message.is_read,
            'replied_to': replied_to_data
        })

    return JsonResponse({'messages': data})

@login_required
@require_POST
def delete_for_me(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if request.user == message.sender:
        message.deleted_for_sender = True
    elif request.user == message.receiver:
        message.deleted_for_receiver = True
    else:
        return JsonResponse({'success': False})

    message.save()

    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_for_everyone(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    # Only the sender can delete for everyone
    if request.user != message.sender:
        return JsonResponse({
            'success': False,
            'error': 'You can only delete your own messages for everyone.'
        })

    message.content = "This message was deleted"
    message.deleted_for_sender = False
    message.deleted_for_receiver = False
    message.save()

    return JsonResponse({'success': True})


@login_required
@require_POST
def remove_user(request, user_id):
    hidden_user = get_object_or_404(User, id=user_id)

    HiddenChat.objects.get_or_create(
        user=request.user,
        hidden_user=hidden_user
    )

    return JsonResponse({'success': True})

@login_required
@require_POST
def delete_user_permanently(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        return JsonResponse({
            'success': False,
            'error': 'You cannot delete your own account.'
        })

    user.delete()

    return JsonResponse({'success': True})