using UnityEngine;

public class Enemy : MonoBehaviour
{
    public int health = 50;
    public int damage = 10;
    public int goldReward = 25;
    public int xpReward = 20;

    private void OnMouseDown()
    {
        TakeDamage(25);
    }

    public void TakeDamage(int amount)
    {
        health -= amount;

        Debug.Log($"inimigo tomou {amount} de dano, HP atual: {health}");

        if (health <= 0)
        {
            Die();
        }
    }

    private void Die()
    {
        PlayerStats player = FindAnyObjectByType<PlayerStats>();

        if (player != null)
        {
            player.AddGold(goldReward);
            player.AddXP(xpReward);

            Debug.Log($"player matou inimigo e recebeu {goldReward} gold e {xpReward} XP");
        }

        Destroy(gameObject);
    }
}