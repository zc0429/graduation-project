package com.example.wrongbook.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.wrongbook.entity.Question;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public interface QuestionMapper extends BaseMapper<Question> {

    /** 在短事务内锁定正常题目，防止派生数据基于过期输入回写。 */
    @Select("SELECT * FROM question WHERE id = #{id} AND status = 1 FOR UPDATE")
    Question selectByIdForUpdate(@Param("id") Long id);

    /** 按知识点分组统计掌握度（学情报告，论文 5.4 自定义聚合 SQL） */
    List<Map<String, Object>> selectKpMastery(@Param("userId") Long userId);

    /** 按日统计新增错题数（since 起） */
    List<Map<String, Object>> selectDailyCount(@Param("userId") Long userId, @Param("since") LocalDateTime since);
}
