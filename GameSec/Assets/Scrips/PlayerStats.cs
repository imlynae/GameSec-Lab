using UnityEngine;

public class PlayerStats : MonoBehaviour
{
    public int health = 100;
    public int gold = 100;
    public int xp = 0;
    public int level = 1;

    public void AddGold(int amount)
    {
        gold += amount;
    }

    public void TakeDamage(int damage)
    {
        health -= damage;
    }

    public void AddXP(int amount)
    {
        xp += amount;
    }
}