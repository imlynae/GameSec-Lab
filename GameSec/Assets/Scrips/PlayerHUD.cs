using TMPro;
using UnityEngine;

public class PlayerHUD : MonoBehaviour
{
    public PlayerStats player;
    public TMP_Text statsText;

    void Update()
    {
        statsText.text =
            $"HP: {player.health}\n" +
            $"Gold: {player.gold}\n" +
            $"XP: {player.xp}\n" +
            $"Level: {player.level}";
    }
}