using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class Task1 : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI word;
    [SerializeField] private TextMeshProUGUI word_counter;
    [SerializeField] private UDP_Listener udp_listener;
    [SerializeField] private TaskManager taskManager;
    [SerializeField] private GameObject cubeLeft;
    [SerializeField] private GameObject cubeRight;
    [SerializeField] private GameObject taskParent;

    private Color highlight_red = new Color(1f, 0.49f, 0.49f);
    private Color highlight_green = new Color(0.45f, 0.95f, 0.55f);
    private Color original_red = new Color(1f, 0f, 0f);
    private Color original_green = new Color(0f, 1f, 0.2f);

    private Vector3 cubeLeftOriginalScale;
    private Vector3 cubeRightOriginalScale;

    private int word_count = 0;
    private string[] words = { "cat", "dog", "chair", "book", "monkey", "computer", "lion", "elephant", "desk", "pencil" };
    private int[] types = { 1, 1, 0, 0, 1, 0, 1, 1, 0, 0 }; // 1 animal, 0 object

    private int leftCount = 0;
    private int rightCount = 0;
    private bool awaitingInput = false;

    public void StartTask()
    {
        cubeLeftOriginalScale = cubeLeft.transform.localScale;
        cubeRightOriginalScale = cubeRight.transform.localScale;

        word_count = 0;

        udp_listener.OnClassReceived += HandleClassInput; // subscribe
        StartCoroutine(WordLoop());
    }

    public void Hide()
    {
        taskParent.SetActive(false);
    }

    public void Show()
    {
        taskParent.SetActive(true);
    }

    private IEnumerator WordLoop()
    {
        while (word_count < words.Length)
        {
            leftCount = 0;
            rightCount = 0;

            word.text = words[word_count];
            word_counter.text = $"Word {word_count + 1} of {words.Length}";

            ResetCubes();

            awaitingInput = true;

            // Wait until one side is selected
            yield return new WaitUntil(() => leftCount >= 2 || rightCount >= 2);

            if (leftCount >= 2)
                Highlight("l");
            else if (rightCount >= 2)
                Highlight("r");

            awaitingInput = false;

            yield return new WaitForSeconds(1.5f);
            word_count++;
        }

        udp_listener.OnClassReceived -= HandleClassInput; // unsubscribe
        taskManager.IntermediatePanel();
        taskParent.SetActive(false);
        this.gameObject.SetActive(false);
    }

    private void HandleClassInput(string input)
    {
        if (!awaitingInput) return;

        if (input == "l")
            leftCount++;
        else if (input == "r")
            rightCount++;
    }

    private void Highlight(string side)
    {
        if (side == "l")
        {
            cubeLeft.transform.localScale = cubeLeftOriginalScale * 1.2f;
            cubeLeft.GetComponent<Renderer>().material.color = highlight_red;

            Debug.Log(types[word_count] == 0 ? "Correct!" : "Incorrect.");
        }
        else if (side == "r")
        {
            cubeRight.transform.localScale = cubeRightOriginalScale * 1.2f;
            cubeRight.GetComponent<Renderer>().material.color = highlight_green;

            Debug.Log(types[word_count] == 1 ? "Correct!" : "Incorrect.");
        }
    }

    private void ResetCubes()
    {
        cubeLeft.transform.localScale = cubeLeftOriginalScale;
        cubeRight.transform.localScale = cubeRightOriginalScale;

        cubeLeft.GetComponent<Renderer>().material.color = original_red;
        cubeRight.GetComponent<Renderer>().material.color = original_green;
    }
}
