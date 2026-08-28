package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.Message;
import com.example.wrongbook.mapper.MessageMapper;
import com.example.wrongbook.service.MessageService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class MessageServiceImpl implements MessageService {

    private final MessageMapper messageMapper;

    @Override
    public void send(Long userId, String type, String title, String content) {
        Message message = new Message();
        message.setUserId(userId);
        message.setType(type);
        message.setTitle(title);
        message.setContent(content);
        messageMapper.insert(message);
    }

    @Override
    public Page<Message> page(Integer pageNum, Integer pageSize, Integer isRead) {
        return messageMapper.selectPage(new Page<>(pageNum, pageSize),
                new LambdaQueryWrapper<Message>()
                        .eq(Message::getUserId, UserContext.getUserId())
                        .eq(isRead != null, Message::getIsRead, isRead)
                        .orderByDesc(Message::getCreateTime));
    }

    @Override
    public void markRead(Long id) {
        Message message = messageMapper.selectById(id);
        if (message == null) {
            throw new BizException(ResultCode.NOT_FOUND.getCode(), "消息不存在");
        }
        if (!message.getUserId().equals(UserContext.getUserId())) {
            throw new BizException(ResultCode.FORBIDDEN.getCode(), "无权操作该消息");
        }
        message.setIsRead(1);
        messageMapper.updateById(message);
    }

    @Override
    public Long unreadCount() {
        return messageMapper.selectCount(new LambdaQueryWrapper<Message>()
                .eq(Message::getUserId, UserContext.getUserId())
                .eq(Message::getIsRead, 0));
    }
}
