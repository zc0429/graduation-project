package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.AnnouncementRequest;
import com.example.wrongbook.entity.Announcement;
import com.example.wrongbook.mapper.AnnouncementMapper;
import com.example.wrongbook.service.AnnouncementService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AnnouncementServiceImpl implements AnnouncementService {

    private final AnnouncementMapper announcementMapper;

    @Override
    public List<Announcement> list() {
        return announcementMapper.selectList(new LambdaQueryWrapper<Announcement>()
                .eq(Announcement::getStatus, 1)
                .orderByDesc(Announcement::getCreateTime));
    }

    @Override
    public Long publish(AnnouncementRequest request) {
        Announcement announcement = new Announcement();
        announcement.setTitle(request.getTitle());
        announcement.setContent(request.getContent());
        announcement.setPublisherId(UserContext.getUserId());
        announcementMapper.insert(announcement);
        return announcement.getId();
    }
}
