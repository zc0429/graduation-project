package com.example.wrongbook.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 公告表（补充表，对应接口表 5.9 公告管理）
 */
@Data
@TableName("announcement")
public class Announcement {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;

    private String content;

    /** 发布人 */
    private Long publisherId;

    /** 状态：1 正常，0 下线 */
    private Integer status;

    private LocalDateTime createTime;
}
