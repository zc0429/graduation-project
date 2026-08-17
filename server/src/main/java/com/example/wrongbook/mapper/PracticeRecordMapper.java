package com.example.wrongbook.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.wrongbook.entity.PracticeRecord;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public interface PracticeRecordMapper extends BaseMapper<PracticeRecord> {

    /** 按日统计练习数（since 起） */
    List<Map<String, Object>> selectDailyCount(@Param("userId") Long userId, @Param("since") LocalDateTime since);
}
