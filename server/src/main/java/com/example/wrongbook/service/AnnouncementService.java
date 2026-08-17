package com.example.wrongbook.service;

import com.example.wrongbook.dto.AnnouncementRequest;
import com.example.wrongbook.entity.Announcement;

import java.util.List;

public interface AnnouncementService {

    /** 公告列表（全部登录用户） */
    List<Announcement> list();

    /** 发布公告（管理员） */
    Long publish(AnnouncementRequest request);
}
